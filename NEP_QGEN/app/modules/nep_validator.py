from typing import Dict, List, Any
import json


class NEPValidator:
    def __init__(self):
        self.nep_guidelines = {
            "cognitive_distribution": {
                "remember": {"min": 15, "max": 25},
                "understand": {"min": 20, "max": 30},
                "apply": {"min": 20, "max": 30},
                "analyze": {"min": 10, "max": 20},
                "evaluate": {"min": 5, "max": 15},
                "create": {"min": 0, "max": 10}
            },
            "question_type_limits": {
                "mcq_max_percentage": 30,
                "application_based_min": 40,
                "case_study_recommended": True
            },
            "assessment_principles": {
                "competency_based": True,
                "holistic_evaluation": True,
                "critical_thinking": True,
                "real_world_application": True
            }
        }

    def validate_paper(self, questions: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate question paper against NEP 2020 guidelines"""

        validation_result = {
            "overall_score": 0,
            "cognitive_distribution_score": 0,
            "question_type_score": 0,
            "competency_score": 0,
            "recommendations": [],
            "compliance_percentage": 0,
            "detailed_analysis": {}
        }

        # Analyze cognitive distribution
        cognitive_analysis = self._analyze_cognitive_distribution(questions)
        validation_result["cognitive_distribution_score"] = cognitive_analysis["score"]
        validation_result["detailed_analysis"]["cognitive"] = cognitive_analysis

        # Analyze question types
        question_type_analysis = self._analyze_question_types(questions)
        validation_result["question_type_score"] = question_type_analysis["score"]
        validation_result["detailed_analysis"]["question_types"] = question_type_analysis

        # Analyze competency-based features
        competency_analysis = self._analyze_competency_features(questions)
        validation_result["competency_score"] = competency_analysis["score"]
        validation_result["detailed_analysis"]["competency"] = competency_analysis

        # Calculate overall score
        validation_result["overall_score"] = (
                validation_result["cognitive_distribution_score"] * 0.4 +
                validation_result["question_type_score"] * 0.3 +
                validation_result["competency_score"] * 0.3
        )

        validation_result["compliance_percentage"] = validation_result["overall_score"]

        # Generate recommendations
        validation_result["recommendations"] = self._generate_recommendations(validation_result)

        return validation_result

    def _analyze_cognitive_distribution(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cognitive level distribution"""

        cognitive_counts = {level: 0 for level in self.nep_guidelines["cognitive_distribution"].keys()}
        total_questions = len(questions)

        for question in questions:
            cognitive_level = question.get("cognitive_level", "understand")
            if cognitive_level in cognitive_counts:
                cognitive_counts[cognitive_level] += 1

        # Calculate percentages
        cognitive_percentages = {
            level: (count / total_questions * 100) if total_questions > 0 else 0
            for level, count in cognitive_counts.items()
        }

        # Check compliance
        compliance_score = 0
        issues = []

        for level, percentage in cognitive_percentages.items():
            guidelines = self.nep_guidelines["cognitive_distribution"][level]
            if guidelines["min"] <= percentage <= guidelines["max"]:
                compliance_score += 1
            else:
                if percentage < guidelines["min"]:
                    issues.append(
                        f"{level.title()} level questions are {guidelines['min'] - percentage:.1f}% below minimum")
                else:
                    issues.append(
                        f"{level.title()} level questions are {percentage - guidelines['max']:.1f}% above maximum")

        score = (compliance_score / len(self.nep_guidelines["cognitive_distribution"])) * 100

        return {
            "score": score,
            "distribution": cognitive_percentages,
            "issues": issues,
            "recommendations": self._get_cognitive_recommendations(cognitive_percentages)
        }

    def _analyze_question_types(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze question type distribution"""

        type_counts = {}
        total_questions = len(questions)

        for question in questions:
            q_type = question.get("type", "unknown")
            type_counts[q_type] = type_counts.get(q_type, 0) + 1

        # Calculate percentages
        type_percentages = {
            q_type: (count / total_questions * 100) if total_questions > 0 else 0
            for q_type, count in type_counts.items()
        }

        score = 100
        issues = []

        # Check MCQ percentage
        mcq_percentage = type_percentages.get("mcq", 0)
        if mcq_percentage > self.nep_guidelines["question_type_limits"]["mcq_max_percentage"]:
            score -= 20
            issues.append(f"MCQ percentage ({mcq_percentage:.1f}%) exceeds recommended maximum (30%)")

        # Check application-based questions
        application_types = ["application", "case_study", "problem_solving"]
        application_percentage = sum(type_percentages.get(t, 0) for t in application_types)

        if application_percentage < self.nep_guidelines["question_type_limits"]["application_based_min"]:
            score -= 25
            issues.append(f"Application-based questions ({application_percentage:.1f}%) below minimum (40%)")

        return {
            "score": max(0, score),
            "distribution": type_percentages,
            "issues": issues
        }

    def _analyze_competency_features(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze competency-based assessment features"""

        competency_score = 0
        features_found = []

        # Check for real-world application
        real_world_count = sum(1 for q in questions
                               if any(keyword in q.get("text", "").lower()
                                      for keyword in ["real-world", "practical", "scenario", "case", "example"]))

        if real_world_count / len(questions) >= 0.3:
            competency_score += 25
            features_found.append("Good real-world application")

        # Check for critical thinking
        critical_thinking_count = sum(1 for q in questions
                                      if any(keyword in q.get("text", "").lower()
                                             for keyword in ["analyze", "evaluate", "compare", "justify", "critique"]))

        if critical_thinking_count / len(questions) >= 0.2:
            competency_score += 25
            features_found.append("Promotes critical thinking")

        # Check for varied assessment methods
        unique_types = len(set(q.get("type", "") for q in questions))
        if unique_types >= 3:
            competency_score += 25
            features_found.append("Diverse assessment methods")

        # Check for holistic evaluation
        high_order_thinking = sum(1 for q in questions
                                  if q.get("cognitive_level", "") in ["analyze", "evaluate", "create"])

        if high_order_thinking / len(questions) >= 0.25:
            competency_score += 25
            features_found.append("Encourages higher-order thinking")

        return {
            "score": competency_score,
            "features_found": features_found
        }

    def _get_cognitive_recommendations(self, percentages: Dict[str, float]) -> List[str]:
        """Generate recommendations for cognitive distribution"""
        recommendations = []

        for level, percentage in percentages.items():
            guidelines = self.nep_guidelines["cognitive_distribution"][level]
            if percentage < guidelines["min"]:
                recommendations.append(f"Increase {level} level questions to at least {guidelines['min']}%")
            elif percentage > guidelines["max"]:
                recommendations.append(f"Reduce {level} level questions to maximum {guidelines['max']}%")

        return recommendations

    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []

        if validation_result["overall_score"] < 70:
            recommendations.append("Paper needs significant improvement for NEP 2020 compliance")

        if validation_result["cognitive_distribution_score"] < 80:
            recommendations.extend(validation_result["detailed_analysis"]["cognitive"]["recommendations"])

        if validation_result["question_type_score"] < 80:
            recommendations.extend(validation_result["detailed_analysis"]["question_types"]["issues"])

        if validation_result["competency_score"] < 70:
            recommendations.append("Include more competency-based and application-oriented questions")
            recommendations.append("Add real-world scenarios and case studies")

        return recommendations
