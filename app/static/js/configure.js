// Configuration page functionality
let questionSets = [];
let totalMarks = 0;

document.addEventListener('DOMContentLoaded', function() {
    console.log("Configure.js loaded"); // Debug log
    
    const form = document.getElementById('paperConfigForm');
    const difficultySlider = document.getElementById('difficulty');
    const difficultyValue = document.getElementById('difficultyValue');
    const addQuestionSetBtn = document.getElementById('addQuestionSet');
    const totalMarksSelect = document.getElementById('total_marks');

    // Check if session_id exists
    const sessionIdInput = document.querySelector('input[name="session_id"]');
    if (sessionIdInput) {
        console.log("Session ID found:", sessionIdInput.value);
    } else {
        console.error("Session ID input not found!");
    }

    // Initialize with one question set
    addQuestionSet();

    // Update difficulty value display
    if (difficultySlider && difficultyValue) {
        difficultySlider.addEventListener('input', function() {
            difficultyValue.textContent = this.value;
        });
    }

    // Add question set button
    if (addQuestionSetBtn) {
        addQuestionSetBtn.addEventListener('click', addQuestionSet);
    }

    // Handle form submission
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }

    // Handle topic tags
    setupTopicTags();

    // Update total marks when target changes
    if (totalMarksSelect) {
        totalMarksSelect.addEventListener('change', updateMarksValidation);
    }

    function addQuestionSet() {
        console.log("Adding question set"); // Debug log
        
        const questionSetsContainer = document.getElementById('questionSets');
        if (!questionSetsContainer) {
            console.error("Question sets container not found!");
            return;
        }
        
        const setIndex = questionSets.length;
        
        const questionSet = {
            id: setIndex,
            type: 'short',
            marks: 5,
            count: 1
        };
        
        questionSets.push(questionSet);
        
        const setElement = document.createElement('div');
        setElement.className = 'question-set bg-gray-50 p-4 rounded-lg';
        setElement.dataset.setId = setIndex;
        
        setElement.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-medium text-gray-900">Question Set ${setIndex + 1}</h4>
                <button type="button" onclick="removeQuestionSet(${setIndex})" 
                        class="text-red-600 hover:text-red-800 text-sm">
                    <i class="fas fa-trash mr-1"></i>Remove
                </button>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Question Type</label>
                    <select name="q_type_${setIndex}" onchange="updateQuestionSet(${setIndex}, 'type', this.value)"
                            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="mcq">Multiple Choice (MCQ)</option>
                        <option value="short" selected>Short Answer</option>
                        <option value="medium">Medium Answer</option>
                        <option value="long">Long Answer</option>
                        <option value="numerical">Numerical Problem</option>
                        <option value="case_study">Case Study</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Marks per Question</label>
                    <select name="q_marks_${setIndex}" onchange="updateQuestionSet(${setIndex}, 'marks', parseInt(this.value))"
                            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="1">1 Mark</option>
                        <option value="2">2 Marks</option>
                        <option value="3">3 Marks</option>
                        <option value="4">4 Marks</option>
                        <option value="5" selected>5 Marks</option>
                        <option value="6">6 Marks</option>
                        <option value="7">7 Marks</option>
                        <option value="8">8 Marks</option>
                        <option value="10">10 Marks</option>
                        <option value="15">15 Marks</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Number of Questions</label>
                    <input type="number" name="q_count_${setIndex}" value="1" min="1" max="20"
                           onchange="updateQuestionSet(${setIndex}, 'count', parseInt(this.value))"
                           class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
            </div>
            
            <div class="mt-3 text-sm text-gray-600">
                <span class="font-medium">Total marks for this set: </span>
                <span id="setMarks_${setIndex}" class="font-bold text-blue-600">5</span>
            </div>
        `;
        
        questionSetsContainer.appendChild(setElement);
        updateTotalMarks();
    }

    function setupTopicTags() {
        const topicTags = document.querySelectorAll('.topic-tag');
        const priorityInput = document.getElementById('priority_topics');
        let selectedTopics = [];

        topicTags.forEach(tag => {
            tag.addEventListener('click', function() {
                const topic = this.dataset.topic;
                
                if (selectedTopics.includes(topic)) {
                    selectedTopics = selectedTopics.filter(t => t !== topic);
                    this.classList.remove('bg-blue-200');
                    this.classList.add('bg-gray-200');
                } else {
                    selectedTopics.push(topic);
                    this.classList.remove('bg-gray-200');
                    this.classList.add('bg-blue-200');
                }
                
                if (priorityInput) {
                    priorityInput.value = selectedTopics.join(', ');
                }
            });
        });
    }

    function handleSubmit(e) {
        e.preventDefault();
        console.log("Form submission started");
        
        // Get session ID
        const sessionIdInput = document.querySelector('input[name="session_id"]');
        if (!sessionIdInput || !sessionIdInput.value) {
            console.error("Session ID not found!");
            showNotification('Session expired. Please start over.', 'error');
            return;
        }
        
        const sessionId = sessionIdInput.value;
        console.log("Using session ID:", sessionId);
        
        // Validate configuration
        if (questionSets.length === 0) {
            showNotification('Please add at least one question set.', 'error');
            return;
        }

        const targetMarks = parseInt(document.getElementById('total_marks').value);
        if (Math.abs(totalMarks - targetMarks) > 5) {
            showNotification(`Total marks (${totalMarks}) should be close to target marks (${targetMarks}).`, 'error');
            return;
        }

        // Prepare form data
        const formData = new FormData();
        
        // Add all form fields
        formData.append('title', document.getElementById('title').value || 'Generated Paper');
        formData.append('subject', document.getElementById('subject').value || 'General Subject');
        formData.append('total_marks', document.getElementById('total_marks').value || '100');
        formData.append('difficulty', document.getElementById('difficulty').value || '5');
        formData.append('priority_topics', document.getElementById('priority_topics').value || '');
        formData.append('instructions', document.getElementById('instructions').value || '');
        
        // Add question configuration as JSON
        const questionConfig = {
            question_sets: questionSets.map(set => ({
                type: set.type,
                marks: set.marks,
                count: set.count
            }))
        };
        
        formData.append('question_config', JSON.stringify(questionConfig));
        
        console.log("Question config:", questionConfig);

        // Show loading
        const loadingModal = document.getElementById('loading');
        if (loadingModal) {
            loadingModal.style.display = 'flex';
        }
        
        // Simulate progress
        const progressBar = document.getElementById('generateProgress');
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 80) progress = 80;
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
        }, 1000);

        // Submit form
        fetch(`/generate/${sessionId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log("Response received:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Response data:", data);
            clearInterval(progressInterval);
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            
            if (data.status === 'success') {
                showNotification('Question paper generated successfully!', 'success');
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1500);
            } else {
                throw new Error(data.message || 'Generation failed');
            }
        })
        .catch(error => {
            console.error('Generation error:', error);
            clearInterval(progressInterval);
            showNotification('Generation failed: ' + error.message, 'error');
            
            if (loadingModal) {
                loadingModal.style.display = 'none';
            }
        });
    }

    function updateTotalMarks() {
        totalMarks = questionSets.reduce((sum, set) => sum + (set.marks * set.count), 0);
        const display = document.getElementById('totalMarksDisplay');
        if (display) {
            display.textContent = totalMarks;
        }
        updateMarksValidation();
    }

    function updateMarksValidation() {
        const targetMarks = parseInt(document.getElementById('total_marks').value);
        const display = document.getElementById('totalMarksDisplay');
        
        if (display) {
            if (Math.abs(totalMarks - targetMarks) <= 5) {
                display.className = 'text-green-600 font-bold';
            } else {
                display.className = 'text-red-600 font-bold';
            }
        }
    }

    // Global functions
    window.updateQuestionSet = function(setIndex, property, value) {
        console.log(`Updating set ${setIndex}: ${property} = ${value}`);
        if (questionSets[setIndex]) {
            questionSets[setIndex][property] = value;
            
            // Update set marks display
            const set = questionSets[setIndex];
            const setMarksElement = document.getElementById(`setMarks_${setIndex}`);
            if (setMarksElement) {
                setMarksElement.textContent = set.marks * set.count;
            }
            
            updateTotalMarks();
        }
    };

    window.removeQuestionSet = function(setIndex) {
        if (questionSets.length <= 1) {
            showNotification('At least one question set is required.', 'error');
            return;
        }
        
        // Remove from array
        questionSets = questionSets.filter(set => set.id !== setIndex);
        
        // Remove from DOM
        const setElement = document.querySelector(`[data-set-id="${setIndex}"]`);
        if (setElement) {
            setElement.remove();
        }
        
        updateTotalMarks();
    };
});
