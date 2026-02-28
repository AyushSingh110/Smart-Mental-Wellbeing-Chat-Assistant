class MentalHealthMatrix:
    def __init__(self):
        self.weights = {
            "E": 0.30,
            "C": 0.35,
            "S": 0.15,
            "B": 0.10,
            "H": 0.10
        }

    def compute(self, emotion_score, crisis_score, scale_score=0, behavior=0, history=0):
        trs = (
            self.weights["E"] * emotion_score +
            self.weights["C"] * crisis_score +
            self.weights["S"] * scale_score +
            self.weights["B"] * behavior +
            self.weights["H"] * history
        )

        mhi = max(0, min(100, 100 * (1 - trs)))
        return round(mhi, 2)

    def categorize(self, mhi, crisis_score):
        if crisis_score >= 0.75:
            return "Crisis"
        if mhi >= 80:
            return "Normal"
        if mhi >= 60:
            return "Mild Stress"
        if mhi >= 40:
            return "Anxiety Risk"
        if mhi >= 20:
            return "Depression Risk"
        return "Crisis"