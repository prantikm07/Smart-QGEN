import google.generativeai as genai
import json
import os
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

class QuestionGenerator:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # NEP 2020 guidelines for AI prompting
        self.nep_guidelines = {
            "cognitive_levels": {
                "remember": 20,
                "understand": 25,
                "apply": 25,
                "analyze": 15,
                "evaluate": 10,
                "create": 5
            }
        }
    
    async def structure_syllabus_with_raw_response(self, raw_text: str) -> Tuple[Dict[str, Any], str]:
        """Use AI to analyze and structure the syllabus text"""
        
        print(f"🤖 Analyzing {len(raw_text)} characters of syllabus text with AI...")
        print(f"📄 Preview: {raw_text[:200]}...")
        
        try:
            prompt = f"""
            Analyze the following syllabus text and extract the structure, topics, and learning objectives.
            DO NOT assume any subject - determine it from the actual content provided.
            
            SYLLABUS TEXT:
            {raw_text}
            
            Based on the above text, create a structured JSON response with:
            1. Subject name (extracted from the text)
            2. Main topics and subtopics (from the syllabus content)
            3. Learning objectives (based on what's mentioned)
            4. Suggested question patterns for assessment
            
            Return ONLY valid JSON:
            {
                "subject": "Subject name from the syllabus text",
                "topics": [
                    {
                        "name": "Topic name from syllabus",
                        "subtopics": ["subtopic1", "subtopic2"],
                        "importance": "high",
                        "cognitive_level": "understand"
                    }
                ],
                "learning_objectives": ["objectives extracted from syllabus"],
                "question_patterns": [
                    {
                        "type": "short",
                        "marks": 5,
                        "count": 4,
                        "topics": ["relevant topics"]
                    }
                ],
                "difficulty_areas": ["challenging topics from syllabus"],
                "key_concepts": ["main concepts from the text"]
            }
            """
            
            print("🤖 Sending syllabus to Gemini for analysis...")
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            
            print(f"🤖 AI Response received ({len(json_text)} chars)")
            print(f"📄 Response preview: {json_text[:200]}...")
            
            # Clean JSON response
            if json_text.startswith('```json'):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith('```'):
                json_text = json_text[3:-3].strip()
            
            structured_data = json.loads(json_text)
            print(f"✅ AI successfully analyzed syllabus: {structured_data.get('subject', 'Unknown Subject')}")
            
            return structured_data, json_text
            
        except Exception as e:
            print(f"❌ AI syllabus analysis failed: {e}")
            print("🔄 Creating minimal fallback structure...")
            
            # Simple text analysis fallback
            lines = raw_text.split('\n')
            subject = "Unknown Subject"
            for line in lines[:10]:
                if len(line.strip()) > 5 and len(line.strip()) < 100:
                    subject = line.strip()
                    break
            
            fallback_data = {
                "subject": subject,
                "topics": [{"name": "General Topics", "subtopics": [], "importance": "medium", "cognitive_level": "understand"}],
                "learning_objectives": ["Understand the subject matter"],
                "question_patterns": [{"type": "short", "marks": 5, "count": 4, "topics": ["General"]}],
                "difficulty_areas": ["Advanced concepts"],
                "key_concepts": ["Core principles"]
            }
            return fallback_data, json.dumps(fallback_data) # Return fallback data and its JSON string
    
    async def generate_questions(
        self,
        syllabus: Dict[str, Any],
        config: Dict[str, Any],
        difficulty: int,
        priority_topics: List[str] = [],
        instructions: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate questions using AI based on syllabus content"""
        
        print(f"🚀 Starting AI question generation...")
        print(f"📚 Subject: {syllabus.get('subject', 'Unknown')}")
        print(f"🎯 Topics: {[t.get('name', '') for t in syllabus.get('topics', [])]}")
        
        all_questions = []
        
        try:
            question_sets = config.get("question_sets", [])
            if not question_sets:
                question_sets = [{"type": "short", "marks": 5, "count": 4}]
            
            for i, question_set in enumerate(question_sets):
                print(f"🔄 Generating question set {i+1}: {question_set}")
                
                questions = await self._generate_ai_questions(
                    syllabus=syllabus,
                    question_type=question_set.get("type", "short"),
                    marks=question_set.get("marks", 5),
                    count=question_set.get("count", 1),
                    difficulty=difficulty,
                    priority_topics=priority_topics,
                    instructions=instructions
                )
                
                all_questions.extend(questions)
                print(f"✅ Set {i+1} complete: {len(questions)} questions")
            
            print(f"🎯 Total AI-generated questions: {len(all_questions)}")
            return all_questions
            
        except Exception as e:
            print(f"❌ AI question generation failed: {e}")
            import traceback
            traceback.print_exc()
            return [self._create_minimal_fallback(syllabus, difficulty)]
    
    async def _generate_ai_questions(
        self,
        syllabus: Dict[str, Any],
        question_type: str,
        marks: int,
        count: int,
        difficulty: int,
        priority_topics: List[str],
        instructions: str
    ) -> List[Dict[str, Any]]:
        """Use AI to generate specific questions from syllabus content"""
        
        subject = syllabus.get("subject", "Unknown Subject")
        topics = syllabus.get("topics", [])
        key_concepts = syllabus.get("key_concepts", [])
        learning_objectives = syllabus.get("learning_objectives", [])
        
        # Create topic focus
        focus_topics = priority_topics if priority_topics else [t.get("name", "") for t in topics[:5]]
        
        try:
            prompt = f"""
            You are an expert educator creating {question_type} questions for {subject}.
            
            SYLLABUS INFORMATION:
            Subject: {subject}
            Topics: {[t.get('name', '') for t in topics]}
            Key Concepts: {key_concepts}
            Learning Objectives: {learning_objectives}
            Focus Topics: {focus_topics}
            
            REQUIREMENTS:
            - Generate {count} {question_type} questions
            - Each question worth {marks} marks
            - Difficulty level: {difficulty}/10
            - Questions should test understanding of the actual syllabus content
            - Follow NEP 2020 guidelines (competency-based, application-focused)
            - Additional instructions: {instructions}
            
            COGNITIVE LEVEL GUIDANCE:
            - MCQ (1-2 marks): Remember/Understand level
            - Short (3-5 marks): Understand/Apply level  
            - Medium (6-10 marks): Apply/Analyze level
            - Long (10+ marks): Analyze/Evaluate/Create level
            
            Generate questions that are:
            1. Specific to the syllabus content provided
            2. Appropriate for the difficulty level
            3. Test practical understanding and application
            4. Include real-world scenarios where applicable
            
            Return ONLY valid JSON array:
            [
                {
                    "text": "Specific question based on syllabus content",
                    "type": "{question_type}",
                    "marks": {marks},
                    "difficulty": {difficulty},
                    "topic": "Relevant topic from syllabus",
                    "cognitive_level": "{self._get_cognitive_level(question_type, marks, difficulty)}",
                    "answer": "Expected answer or solution approach",
                    "marking_scheme": ["Complete answer: {marks} marks"],
                    "options": {json.dumps(["Option A", "Option B", "Option C", "Option D"]) if question_type == "mcq" else "null"}
                }
            ]
            """
            
            print(f"🤖 Generating {count} {question_type} questions with AI...")
            
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            
            print(f"🤖 AI response received ({len(json_text)} chars)")
            
            # Clean JSON response
            if json_text.startswith('```json'):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith('```'):
                json_text = json_text[3:-3].strip()
            
            questions = json.loads(json_text)
            
            # Ensure we have a list
            if not isinstance(questions, list):
                questions = [questions] if isinstance(questions, dict) else []
            
            # Validate and fix questions
            validated_questions = []
            for q in questions:
                if isinstance(q, dict) and q.get("text"):
                    # Ensure all required fields exist
                    validated_q = {
                        "text": q.get("text", "Generated question"),
                        "type": question_type,
                        "marks": marks,
                        "difficulty": difficulty,
                        "topic": q.get("topic", "General Topic"),
                        "cognitive_level": q.get("cognitive_level", self._get_cognitive_level(question_type, marks, difficulty)),
                        "answer": q.get("answer", "Expected answer"),
                        "marking_scheme": q.get("marking_scheme", [f"Complete answer: {marks} marks"]),
                        "options": q.get("options") if question_type == "mcq" else None
                    }
                    validated_questions.append(validated_q)
                    print(f"✅ AI Question: {validated_q['text'][:60]}...")
            
            # If we don't have enough questions, generate more using fallback
            while len(validated_questions) < count:
                fallback = self._create_minimal_fallback(syllabus, difficulty, question_type)
                validated_questions.append(fallback)
            
            return validated_questions[:count]
            
        except Exception as e:
            print(f"❌ AI question generation error: {e}")
            # Return minimal fallbacks
            return [self._create_minimal_fallback(syllabus, difficulty, question_type) for _ in range(count)]
    
    def _create_minimal_fallback(self, syllabus: Dict[str, Any], difficulty: int, q_type: str = "short") -> Dict[str, Any]:
        """Create minimal fallback when AI fails completely"""
        
        subject = syllabus.get("subject", "Unknown Subject")
        topics = syllabus.get("topics", [])
        topic_name = topics[0].get("name", "General Topic") if topics else "General Topic"
        
        fallback_questions = {
            "mcq": f"Which of the following best describes a key concept in {subject}?",
            "short": f"Explain the fundamental principles of {topic_name} as covered in the syllabus.",
            "medium": f"Analyze the importance and applications of {topic_name} in {subject}.",
            "long": f"Provide a comprehensive discussion of {topic_name}, including its theoretical foundations and practical applications in {subject}."
        }
        
        return {
            "text": fallback_questions.get(q_type, fallback_questions["short"]),
            "type": q_type,
            "marks": 1 if q_type == "mcq" else 5,
            "difficulty": difficulty,
            "topic": topic_name,
            "cognitive_level": self._get_cognitive_level(q_type, 1 if q_type == "mcq" else 5, difficulty),
            "answer": f"Expected comprehensive answer about {topic_name}",
            "marking_scheme": [f"Complete answer: {1 if q_type == 'mcq' else 5} marks"],
            "options": ["Correct option", "Incorrect option 1", "Incorrect option 2", "Incorrect option 3"] if q_type == "mcq" else None
        }
    
    def _get_cognitive_level(self, question_type: str, marks: int, difficulty: int) -> str:
        """Determine appropriate cognitive level"""
        if question_type == "mcq":
            return "remember" if difficulty <= 3 else "understand"
        elif marks <= 2:
            return "understand"
        elif marks <= 5:
            return "apply" if difficulty <= 6 else "analyze"
        else:
            return "evaluate" if difficulty <= 8 else "create"
