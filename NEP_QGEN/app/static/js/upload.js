// File upload functionality
let selectedFiles = [];

document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const uploadBtn = document.getElementById('uploadBtn');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    // Handle click to browse
    dropArea.addEventListener('click', () => fileInput.click());

    // Handle file input change
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    // Handle upload button
    uploadBtn.addEventListener('click', uploadFiles);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropArea.classList.add('dragover');
    }

    function unhighlight(e) {
        dropArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        selectedFiles = Array.from(files);
        updateFilePreview();
        updateUploadButton();
    }

    function updateFilePreview() {
        filePreview.innerHTML = '';

        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';

            fileItem.innerHTML = `
                <div class="flex items-center">
                    <div class="mr-3">
                        ${getFileIcon(file.type)}
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${file.name}</div>
                        <div class="text-sm text-gray-500">${formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button onclick="removeFile(${index})" class="text-red-600 hover:text-red-800">
                    <i class="fas fa-times"></i>
                </button>
            `;

            filePreview.appendChild(fileItem);
        });
    }

    function getFileIcon(fileType) {
        if (fileType.includes('pdf')) {
            return '<i class="fas fa-file-pdf text-red-600 text-xl"></i>';
        } else if (fileType.includes('image')) {
            return '<i class="fas fa-file-image text-green-600 text-xl"></i>';
        } else {
            return '<i class="fas fa-file-alt text-blue-600 text-xl"></i>';
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function updateUploadButton() {
        uploadBtn.disabled = selectedFiles.length === 0;
    }

    function uploadFiles() {
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        // Show progress
        const progressContainer = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        progressContainer.classList.remove('hidden');
        uploadBtn.disabled = true;

        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 500);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';

            if (data.status === 'success') {
                progressText.textContent = 'Processing complete!';
                showNotification('Files uploaded successfully!', 'success');

                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else {
                throw new Error(data.message || 'Upload failed');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            console.error('Upload error:', error);
            showNotification('Upload failed: ' + error.message, 'error');
            progressContainer.classList.add('hidden');
            uploadBtn.disabled = false;
        });
    }

    // Global function to remove files
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFilePreview();
        updateUploadButton();
    };
});
