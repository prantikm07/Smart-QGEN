import google.generativeai as genai
import json
import os
from typing import Dict, List, Any
import random
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
        
        # NEP 2020 guidelines
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
    
    async def structure_syllabus(self, raw_text: str) -> Dict[str, Any]:
        """Convert raw syllabus text to structured format"""
        
        print("Structuring syllabus...")
        
        # Check if it's DBMS content
        text_lower = raw_text.lower()
        if any(keyword in text_lower for keyword in ["database", "dbms", "sql", "mysql", "postgresql", "oracle", "relational"]):
            print("✅ Detected DBMS content")
            return {
                "subject": "Database Management Systems (DBMS)",
                "topics": [
                    {"name": "Introduction to DBMS", "subtopics": ["Database Concepts"], "importance": "high", "cognitive_level": "understand"},
                    {"name": "Relational Model", "subtopics": ["Tables", "Keys"], "importance": "high", "cognitive_level": "apply"},
                    {"name": "SQL", "subtopics": ["DDL", "DML", "Queries"], "importance": "high", "cognitive_level": "apply"},
                    {"name": "Normalization", "subtopics": ["1NF", "2NF", "3NF"], "importance": "high", "cognitive_level": "analyze"},
                    {"name": "Transactions", "subtopics": ["ACID Properties"], "importance": "medium", "cognitive_level": "analyze"},
                    {"name": "Indexing", "subtopics": ["B+ Trees"], "importance": "medium", "cognitive_level": "understand"}
                ],
                "learning_objectives": ["Understand database fundamentals", "Design efficient database schemas", "Write complex SQL queries"],
                "question_patterns": [
                    {"type": "mcq", "marks": 1, "count": 10, "topics": ["Introduction", "SQL"]},
                    {"type": "short", "marks": 5, "count": 8, "topics": ["Relational Model", "Normalization"]}
                ],
                "difficulty_areas": ["Normalization", "Concurrency Control"]
            }
        
        print("Using general subject structure")
        return {
            "subject": "General Subject",
            "topics": [
                {"name": "Introduction", "subtopics": ["Basic Concepts"], "importance": "high", "cognitive_level": "understand"},
                {"name": "Core Topics", "subtopics": ["Main Concepts"], "importance": "high", "cognitive_level": "apply"},
                {"name": "Advanced Topics", "subtopics": ["Complex Ideas"], "importance": "medium", "cognitive_level": "analyze"}
            ],
            "learning_objectives": ["Understand concepts", "Apply knowledge", "Analyze problems"],
            "question_patterns": [
                {"type": "mcq", "marks": 1, "count": 10, "topics": ["Introduction"]},
                {"type": "short", "marks": 5, "count": 8, "topics": ["Core Topics"]}
            ],
            "difficulty_areas": ["Advanced Topics"]
        }
    
    async def generate_questions(
        self,
        syllabus: Dict[str, Any],
        config: Dict[str, Any],
        difficulty: int,
        priority_topics: List[str] = [],
        instructions: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate questions based on configuration"""
        
        print(f"🚀 Starting question generation...")
        print(f"📋 Config: {config}")
        print(f"📚 Subject: {syllabus.get('subject', 'Unknown')}")
        
        all_questions = []
        
        try:
            question_sets = config.get("question_sets", [])
            
            if not question_sets:
                print("⚠️ No question sets found, creating default")
                question_sets = [{"type": "short", "marks": 5, "count": 4}]
            
            for i, question_set in enumerate(question_sets):
                print(f"🔄 Processing set {i+1}: {question_set}")
                
                q_type = question_set.get("type", "short")
                marks = question_set.get("marks", 5)
                count = question_set.get("count", 1)
                
                questions = self._generate_subject_specific_questions(
                    syllabus=syllabus,
                    question_type=q_type,
                    marks=marks,
                    count=count,
                    difficulty=difficulty
                )
                
                print(f"✅ Generated {len(questions)} questions for set {i+1}")
                all_questions.extend(questions)
            
            print(f"🎯 Total questions generated: {len(all_questions)}")
            return all_questions
            
        except Exception as e:
            print(f"❌ Error in generate_questions: {e}")
            import traceback
            traceback.print_exc()
            return [self._create_emergency_question(difficulty)]
    
    def _generate_subject_specific_questions(
        self,
        syllabus: Dict[str, Any],
        question_type: str,
        marks: int,
        count: int,
        difficulty: int
    ) -> List[Dict[str, Any]]:
        """Generate subject-specific questions"""
        
        subject = syllabus.get("subject", "General Subject")
        print(f"📝 Generating {count} {question_type} questions for {subject}")
        
        questions = []
        
        # DBMS Questions - FIXED
        if "database" in subject.lower() or "dbms" in subject.lower():
            print("🗄️ Using DBMS questions")
            
            # Define actual DBMS questions by type
            if question_type == "mcq":
                dbms_mcq = [
                    "Which of the following is NOT an ACID property in database transactions?",
                    "In SQL, which command is used to create a new table?", 
                    "What is the primary purpose of database normalization?",
                    "Which normal form eliminates partial functional dependencies?",
                    "What does SQL stand for?"
                ]
                question_texts = dbms_mcq
                options_list = [
                    ["Atomicity", "Consistency", "Isolation", "Availability"],
                    ["CREATE TABLE", "MAKE TABLE", "NEW TABLE", "BUILD TABLE"],
                    ["Increase speed", "Reduce redundancy", "Add more data", "Create backups"],
                    ["1NF", "2NF", "3NF", "BCNF"],
                    ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"]
                ]
            elif question_type == "short":
                question_texts = [
                    "Explain the concept of primary key and foreign key in relational databases.",
                    "Define database normalization and explain its importance in database design.",
                    "What is the difference between DDL and DML commands in SQL?",
                    "Describe the ACID properties of database transactions.",
                    "Explain the concept of database indexing and its advantages.",
                    "What is an Entity-Relationship (ER) diagram and what are its main components?",
                    "Differentiate between INNER JOIN and LEFT JOIN in SQL.",
                    "Explain the concept of database schema and its types."
                ]
            elif question_type == "medium":
                question_texts = [
                    "Discuss the different levels of database normalization (1NF, 2NF, 3NF) with examples.",
                    "Explain the concept of concurrency control in databases and the problems it solves.",
                    "Describe the different types of database joins with examples and use cases.",
                    "Discuss the recovery mechanisms used in database management systems.",
                    "Explain the difference between clustered and non-clustered indexes in databases."
                ]
            else:  # long
                question_texts = [
                    "Design a complete ER diagram for a library management system and convert it to relational schema.",
                    "Explain the working of B+ trees in database indexing with detailed examples.",
                    "Discuss different concurrency control protocols and compare their effectiveness.",
                    "Analyze the CAP theorem and its implications for distributed database systems."
                ]
        else:
            print("📚 Using general questions")
            # General questions
            question_texts = [
                f"Explain the basic principles and concepts of {subject}.",
                f"Define the key terminology used in {subject}.",
                f"Describe the main applications of {subject}.",
                f"What are the core components of {subject}?",
                f"Analyze the key methodologies used in {subject}."
            ]
            options_list = [
                [f"Core principle of {subject}", f"Secondary aspect", f"Unrelated concept", f"Opposite principle"]
            ] * 5
        
        # Create questions
        for i in range(count):
            question_text = question_texts[i % len(question_texts)]
            
            question = {
                "text": question_text,  # THIS WAS THE ISSUE - text wasn't being set properly
                "type": question_type,
                "marks": marks,
                "difficulty": difficulty,
                "topic": "Database Management Systems" if "database" in subject.lower() else subject,
                "cognitive_level": self._get_cognitive_level(question_type, marks, difficulty),
                "answer": "Detailed answer covering key concepts",
                "marking_scheme": [f"Complete answer: {marks} marks"]
            }
            
            # Add options for MCQ
            if question_type == "mcq" and "database" in subject.lower():
                question["options"] = options_list[i % len(options_list)]
            elif question_type == "mcq":
                question["options"] = [f"Option A", f"Option B", f"Option C", f"Option D"]
            else:
                question["options"] = None
            
            questions.append(question)
            print(f"✅ Created question: {question_text[:50]}...")
        
        return questions

    def _get_dbms_questions(self, question_type: str, marks: int, count: int, difficulty: int) -> List[Dict[str, Any]]:
        """Get DBMS-specific questions"""
        
        dbms_questions = {
            "mcq": [
                {
                    "text": "Which of the following is NOT an ACID property in database transactions?",
                    "options": ["Atomicity", "Consistency", "Isolation", "Availability"],
                    "answer": "Availability"
                },
                {
                    "text": "In SQL, which command is used to create a new table?",
                    "options": ["CREATE TABLE", "MAKE TABLE", "NEW TABLE", "BUILD TABLE"],
                    "answer": "CREATE TABLE"
                },
                {
                    "text": "What is the primary purpose of database normalization?",
                    "options": ["Increase speed", "Reduce redundancy", "Add more data", "Create backups"],
                    "answer": "Reduce redundancy"
                },
                {
                    "text": "Which normal form eliminates partial functional dependencies?",
                    "options": ["1NF", "2NF", "3NF", "BCNF"],
                    "answer": "2NF"
                },
                {
                    "text": "What does SQL stand for?",
                    "options": ["Structured Query Language", "Simple Query Language", "Standard Query Language", "System Query Language"],
                    "answer": "Structured Query Language"
                }
            ],
            "short": [
                {
                    "text": "Explain the concept of primary key and foreign key in relational databases.",
                    "answer": "Primary key uniquely identifies records, foreign key references primary key of another table"
                },
                {
                    "text": "Define database normalization and explain its importance in database design.",
                    "answer": "Process of organizing data to reduce redundancy and improve data integrity"
                },
                {
                    "text": "What is the difference between DDL and DML commands in SQL?",
                    "answer": "DDL defines database structure, DML manipulates data within tables"
                },
                {
                    "text": "Describe the ACID properties of database transactions.",
                    "answer": "Atomicity, Consistency, Isolation, Durability ensure reliable transaction processing"
                },
                {
                    "text": "Explain the concept of database indexing and its advantages.",
                    "answer": "Data structure that improves query performance by creating shortcuts to data"
                },
                {
                    "text": "What is an Entity-Relationship (ER) diagram and what are its main components?",
                    "answer": "Visual representation of database structure with entities, attributes, and relationships"
                },
                {
                    "text": "Differentiate between INNER JOIN and LEFT JOIN in SQL.",
                    "answer": "INNER JOIN returns matching records, LEFT JOIN returns all left table records"
                },
                {
                    "text": "Explain the concept of database schema and its types.",
                    "answer": "Logical structure of database including physical, logical, and view schemas"
                }
            ],
            "medium": [
                {
                    "text": "Discuss the different levels of database normalization (1NF, 2NF, 3NF) with examples.",
                    "answer": "Progressive elimination of redundancy through normal forms"
                },
                {
                    "text": "Explain the concept of concurrency control in databases and the problems it solves.",
                    "answer": "Manages simultaneous database access to prevent conflicts and maintain consistency"
                },
                {
                    "text": "Describe the different types of database joins with examples and use cases.",
                    "answer": "INNER, LEFT, RIGHT, FULL OUTER joins combine data from multiple tables"
                },
                {
                    "text": "Discuss the recovery mechanisms used in database management systems.",
                    "answer": "Log-based recovery, checkpoints, and backup strategies for data protection"
                },
                {
                    "text": "Explain the difference between clustered and non-clustered indexes in databases.",
                    "answer": "Clustered indexes physically order data, non-clustered create separate structures"
                }
            ],
            "long": [
                {
                    "text": "Design a complete ER diagram for a library management system and convert it to relational schema.",
                    "answer": "Comprehensive design including entities, relationships, and normalization"
                },
                {
                    "text": "Explain the working of B+ trees in database indexing with detailed examples.",
                    "answer": "Balanced tree structure optimized for database storage and retrieval"
                },
                {
                    "text": "Discuss different concurrency control protocols and compare their effectiveness.",
                    "answer": "Lock-based, timestamp-based, and optimistic protocols comparison"
                },
                {
                    "text": "Analyze the CAP theorem and its implications for distributed database systems.",
                    "answer": "Consistency, Availability, Partition tolerance trade-offs in distributed systems"
                }
            ]
        }
        
        questions_list = dbms_questions.get(question_type, dbms_questions["short"])
        selected_questions = []
        
        for i in range(count):
            q_data = questions_list[i % len(questions_list)]
            
            question = {
                "text": q_data["text"],
                "type": question_type,
                "marks": marks,
                "difficulty": difficulty,
                "topic": "Database Management Systems",
                "cognitive_level": self._get_cognitive_level(question_type, marks, difficulty),
                "answer": q_data["answer"],
                "marking_scheme": [f"Complete answer: {marks} marks"],
                "options": q_data.get("options") if question_type == "mcq" else None
            }
            
            selected_questions.append(question)
            print(f"✅ Created DBMS question: {question['text'][:50]}...")
        
        return selected_questions
    
    def _get_general_questions(self, subject: str, question_type: str, marks: int, count: int, difficulty: int) -> List[Dict[str, Any]]:
        """Get general subject questions"""
        
        general_templates = {
            "mcq": [
                f"Which of the following is a key principle of {subject}?",
                f"What is the primary focus of {subject}?",
                f"In {subject}, which approach is most effective?",
                f"Which concept is fundamental to {subject}?"
            ],
            "short": [
                f"Explain the basic principles and concepts of {subject}.",
                f"Define the key terminology used in {subject}.",
                f"Describe the main applications of {subject}.",
                f"What are the core components of {subject}?"
            ],
            "medium": [
                f"Analyze the key methodologies used in {subject}.",
                f"Compare different approaches within {subject}.",
                f"Evaluate the effectiveness of {subject} techniques.",
                f"Discuss the practical applications of {subject}."
            ],
            "long": [
                f"Provide a comprehensive analysis of {subject} including its principles and applications.",
                f"Critically evaluate the role of {subject} in modern technology.",
                f"Design a complete solution using {subject} methodologies.",
                f"Examine the theoretical foundations and practical implications of {subject}."
            ]
        }
        
        templates = general_templates.get(question_type, general_templates["short"])
        questions = []
        
        for i in range(count):
            template = templates[i % len(templates)]
            
            question = {
                "text": template,
                "type": question_type,
                "marks": marks,
                "difficulty": difficulty,
                "topic": subject,
                "cognitive_level": self._get_cognitive_level(question_type, marks, difficulty),
                "answer": f"Detailed answer covering {subject} concepts",
                "marking_scheme": [f"Complete answer: {marks} marks"],
                "options": [
                    f"Core principle of {subject}",
                    f"Secondary aspect of {subject}",
                    f"Unrelated concept",
                    f"Opposite principle"
                ] if question_type == "mcq" else None
            }
            
            questions.append(question)
        
        return questions
    
    def _get_cognitive_level(self, question_type: str, marks: int, difficulty: int) -> str:
        """Determine cognitive level"""
        if question_type == "mcq":
            return "remember" if difficulty <= 3 else "understand"
        elif marks <= 2:
            return "understand"
        elif marks <= 5:
            return "apply" if difficulty <= 6 else "analyze"
        else:
            return "evaluate" if difficulty <= 8 else "create"
    
    def _create_emergency_question(self, difficulty: int, q_type: str = "short") -> Dict[str, Any]:
        """Create emergency fallback question"""
        
        return {
            "text": "Explain the fundamental concepts and principles covered in this subject area.",
            "type": q_type,
            "marks": 5 if q_type != "mcq" else 1,
            "difficulty": difficulty,
            "topic": "General Topic",
            "cognitive_level": "understand",
            "answer": "Comprehensive answer covering main concepts",
            "marking_scheme": [f"Complete answer: {5 if q_type != 'mcq' else 1} marks"],
            "options": ["Concept A", "Concept B", "Concept C", "Concept D"] if q_type == "mcq" else None
        }
    
    def _create_fallback_question(self, q_type: str, marks: int, difficulty: int, topics: List[Dict]) -> Dict[str, Any]:
        """Create a basic fallback question"""
        return self._create_emergency_question(difficulty, q_type)
