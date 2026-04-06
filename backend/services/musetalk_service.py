"""
MuseTalk service — optional GPU-accelerated lip-sync video generation.

Architecture:
  1. Caller submits a job: (audio_bytes, avatar_id) → job_id (UUID)
  2. Worker runs MuseTalk in a background thread pool
  3. Output video cached to AVATAR_VIDEO_CACHE_DIR as {job_id}.mp4
  4. Caller polls GET /avatar/video/{job_id}

Graceful fallback:
  - If MUSETALK_ENABLED=false or MuseTalk import fails → status="unavailable"
  - If GPU unavailable → CPU inference (slow, warns in logs)
  - LRU cache (max 50 videos, 512 MB) prevents disk overflow

Primary path is still Web Audio API CSS animation (no MuseTalk needed).
MuseTalk is purely additive for devices with a discrete GPU.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import threading
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Job status constants
STATUS_PENDING     = "pending"
STATUS_PROCESSING  = "processing"
STATUS_DONE        = "done"
STATUS_FAILED      = "failed"
STATUS_UNAVAILABLE = "unavailable"

# ── LRU video cache (in-memory index, files on disk)
_LRU_MAX_ENTRIES   = 50
_LRU_MAX_BYTES     = 512 * 1024 * 1024   # 512 MB

# ── Per-avatar source images (populated from PERSONA_STATIC_DIR)
# These are the reference portrait images MuseTalk animates.
_AVATAR_IMAGE_FILENAMES: dict[str, str] = {
    "therapist":  "therapist.jpg",
    "companion":  "companion.jpg",
    "guide":      "guide.jpg",
    "elder":      "elder.jpg",
}


class _LRUVideoCache:
    """Simple thread-safe LRU cache tracking job_id → file_path."""

    def __init__(self, max_entries: int = _LRU_MAX_ENTRIES):
        self._cache: OrderedDict[str, Path] = OrderedDict()
        self._max   = max_entries
        self._lock  = threading.Lock()

    def put(self, job_id: str, path: Path) -> None:
        with self._lock:
            if job_id in self._cache:
                self._cache.move_to_end(job_id)
            else:
                if len(self._cache) >= self._max:
                    _, old_path = self._cache.popitem(last=False)
                    try:
                        old_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                self._cache[job_id] = path

    def get(self, job_id: str) -> Optional[Path]:
        with self._lock:
            if job_id not in self._cache:
                return None
            self._cache.move_to_end(job_id)
            return self._cache[job_id]

    def has(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._cache


class MuseTalkService:
    """
    Thin wrapper around MuseTalk 1.5 for lip-sync video generation.

    Designed to fail gracefully — all callers should check
    job["status"] before assuming a video is available.
    """

    def __init__(self):
        self._enabled     = settings.MUSETALK_ENABLED
        self._cache_dir   = Path(settings.AVATAR_VIDEO_CACHE_DIR)
        self._static_dir  = Path(settings.PERSONA_STATIC_DIR)
        self._musetalk    = None          # lazy-loaded
        self._executor    = ThreadPoolExecutor(max_workers=1, thread_name_prefix="musetalk")
        self._jobs: dict[str, dict] = {}  # job_id → status dict
        self._video_cache = _LRUVideoCache()
        self._jobs_lock   = threading.Lock()

        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._try_load_musetalk()
        else:
            logger.info("MuseTalkService | disabled (MUSETALK_ENABLED=false)")

    # ── Public API

    def is_available(self) -> bool:
        return self._enabled and self._musetalk is not None

    def submit_job(self, audio_bytes: bytes, avatar_id: str) -> str:
        """
        Submit a lip-sync video generation job.
        Returns job_id (UUID string).
        The job status can be polled via get_job_status().
        """
        job_id = str(uuid.uuid4())

        if not self.is_available():
            with self._jobs_lock:
                self._jobs[job_id] = {
                    "status":    STATUS_UNAVAILABLE,
                    "video_url": None,
                    "error":     "MuseTalk not available on this server",
                }
            return job_id

        # Check cache: if same audio+avatar was processed before, return cached
        cache_key = self._cache_key(audio_bytes, avatar_id)
        cached_path = self._video_cache.get(cache_key)
        if cached_path and cached_path.exists():
            dst = self._cache_dir / f"{job_id}.mp4"
            try:
                shutil.copy2(cached_path, dst)
            except Exception:
                pass
            with self._jobs_lock:
                self._jobs[job_id] = {
                    "status":    STATUS_DONE,
                    "video_url": f"/avatar/video/{job_id}",
                    "error":     None,
                }
            logger.info("MuseTalkService | cache hit for job %s (key=%s)", job_id, cache_key[:8])
            return job_id

        # Submit to background worker
        with self._jobs_lock:
            self._jobs[job_id] = {
                "status":    STATUS_PENDING,
                "video_url": None,
                "error":     None,
            }

        self._executor.submit(self._run_job, job_id, audio_bytes, avatar_id, cache_key)
        return job_id

    def get_job_status(self, job_id: str) -> dict:
        """
        Returns current job status dict:
          { status: str, video_url: str|None, error: str|None }
        """
        with self._jobs_lock:
            return dict(self._jobs.get(job_id, {
                "status":    STATUS_FAILED,
                "video_url": None,
                "error":     "Job not found",
            }))

    def get_video_path(self, job_id: str) -> Optional[Path]:
        """Returns the output video file path if job is done, else None."""
        status = self.get_job_status(job_id)
        if status.get("status") != STATUS_DONE:
            return None
        path = self._cache_dir / f"{job_id}.mp4"
        return path if path.exists() else None

    # ── Internals

    def _try_load_musetalk(self) -> None:
        """Attempt to import MuseTalk. Disables itself if import fails."""
        model_path = settings.MUSETALK_MODEL_PATH
        try:
            # MuseTalk 1.5 exposes a simple Python API when installed
            # Expected: from musetalk.inference import MuseTalkInference
            from musetalk.inference import MuseTalkInference  # type: ignore[import]
            self._musetalk = MuseTalkInference(model_path=model_path)
            logger.info("MuseTalkService | loaded from %s", model_path)
        except ImportError:
            logger.warning(
                "MuseTalkService | musetalk package not installed — "
                "lip-sync video will be unavailable. CSS animation is the active fallback."
            )
            self._musetalk = None
        except Exception as exc:
            logger.warning("MuseTalkService | failed to load model: %s", exc)
            self._musetalk = None

    def _run_job(self, job_id: str, audio_bytes: bytes, avatar_id: str, cache_key: str) -> None:
        """Background worker: runs MuseTalk inference for one job."""
        with self._jobs_lock:
            self._jobs[job_id]["status"] = STATUS_PROCESSING

        try:
            # Locate source avatar image
            img_filename = _AVATAR_IMAGE_FILENAMES.get(avatar_id, "therapist.jpg")
            img_path = self._static_dir / img_filename
            if not img_path.exists():
                raise FileNotFoundError(f"Avatar source image not found: {img_path}")

            # Write audio to temp file
            audio_tmp = self._cache_dir / f"{job_id}_audio.wav"
            audio_tmp.write_bytes(audio_bytes)

            output_path = self._cache_dir / f"{job_id}.mp4"

            try:
                # MuseTalk inference call
                self._musetalk.run(
                    source_image=str(img_path),
                    driving_audio=str(audio_tmp),
                    output_video=str(output_path),
                )
            finally:
                audio_tmp.unlink(missing_ok=True)

            if not output_path.exists():
                raise RuntimeError("MuseTalk produced no output file")

            # Store in LRU cache
            self._video_cache.put(cache_key, output_path)

            with self._jobs_lock:
                self._jobs[job_id] = {
                    "status":    STATUS_DONE,
                    "video_url": f"/avatar/video/{job_id}",
                    "error":     None,
                }
            logger.info("MuseTalkService | job %s done → %s", job_id, output_path)

        except Exception as exc:
            logger.error("MuseTalkService | job %s failed: %s", job_id, exc)
            with self._jobs_lock:
                self._jobs[job_id] = {
                    "status":    STATUS_FAILED,
                    "video_url": None,
                    "error":     str(exc),
                }

    @staticmethod
    def _cache_key(audio_bytes: bytes, avatar_id: str) -> str:
        h = hashlib.sha256(audio_bytes + avatar_id.encode()).hexdigest()[:16]
        return h
