// AI Video Tool Web Application
// Main JavaScript file for the web interface

// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8080' : '';

// Global state
let uploadedFiles = {
    script: null,
    voice: null,
    brollVoice: null,
    brollClips: [],
    introClips: []
};
let ws = null;

// Helper function for API calls
function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Setup tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // Setup dropzones
    setupDropzone('script-dropzone', 'script-file', handleScriptUpload);
    setupDropzone('voice-dropzone', 'voice-file', handleVoiceUpload);
    setupDropzone('broll-dropzone', 'broll-files', handleBrollUpload);
    setupDropzone('intro-dropzone', 'intro-files', handleIntroUpload);
    setupDropzone('broll-voice-dropzone', 'broll-voice-file', handleBrollVoiceUpload);
    
    // Setup event listeners
    setupEventListeners();
    
    // Check API key status for public app
    checkApiKey();
    
}

function setupEventListeners() {
    console.log('🔧 Setting up event listeners...');
    
    // API key button
    document.getElementById('api-key-btn').addEventListener('click', () => {
        showModal('api-key-modal');
        // Check current API key status when opening modal
        checkApiKeyInModal();
    });

    // Form submissions
    document.getElementById('api-key-form').addEventListener('submit', handleApiKey);

    // Generation buttons
    document.getElementById('generate-btn').addEventListener('click', generateAIImages);
    
    // B-Roll organize button
    const organizeBtn = document.getElementById('organize-btn');
    console.log('🎯 Found organize-btn element:', organizeBtn);
    if (organizeBtn) {
        organizeBtn.addEventListener('click', () => {
            console.log('🎬 organize-btn clicked!');
            organizeBroll();
        });
        console.log('✅ Event listener added to organize-btn');
    } else {
        console.error('❌ organize-btn element not found!');
    }
}

async function checkApiKeyInModal() {
    try {
        const response = await fetch(apiUrl('/api/check-api-key'));
        const modalBody = document.querySelector('#api-key-modal form');
        
        // Remove any existing status message
        const existingStatus = modalBody.querySelector('.api-key-status');
        if (existingStatus) existingStatus.remove();
        
        // Add status message
        const statusDiv = document.createElement('div');
        statusDiv.className = 'api-key-status mb-4 p-3 rounded';
        
        if (response.ok) {
            const data = await response.json();
            statusDiv.className += ' bg-green-100 text-green-800';
            statusDiv.innerHTML = `<i class="fas fa-check-circle mr-2"></i>API key is already configured (${data.source})`;
        } else {
            statusDiv.className += ' bg-yellow-100 text-yellow-800';
            statusDiv.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>No API key configured yet';
        }
        
        modalBody.insertBefore(statusDiv, modalBody.firstChild);
    } catch (error) {
        console.error('Error checking API key in modal:', error);
    }
}

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-600');
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    activeBtn.classList.add('active', 'border-blue-500', 'text-blue-600');
    activeBtn.classList.remove('border-transparent', 'text-gray-600');
    
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'jobs') {
        loadJobs();
    }
}

// API Key Management
async function checkApiKey() {
    try {
        const response = await fetch(apiUrl('/api/check-api-key'));
        if (response.ok) {
            updateApiKeyStatus(true);
        } else {
            updateApiKeyStatus(false);
        }
    } catch (error) {
        console.error('Failed to check API key:', error);
        updateApiKeyStatus(false);
    }
}

function updateApiKeyStatus(hasKey) {
    const btn = document.getElementById('api-key-btn');
    if (hasKey) {
        btn.innerHTML = '<i class="fas fa-key mr-2"></i>API Key ✓';
        btn.classList.add('bg-green-200');
        btn.classList.remove('bg-gray-200');
    } else {
        btn.innerHTML = '<i class="fas fa-key mr-2"></i>Set API Key';
        btn.classList.add('bg-gray-200');
        btn.classList.remove('bg-green-200');
    }
}

async function handleApiKey(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const submitButton = e.target.querySelector('button[type="submit"]');
    
    // Disable submit button and show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
    
    try {
        const response = await fetch(apiUrl('/api/settings/api-key'), {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            closeModal('api-key-modal');
            showNotification('API key saved successfully!', 'success');
            checkApiKey();
            // Clear the form
            e.target.reset();
        } else {
            const error = await response.text();
            showNotification('Failed to save API key: ' + error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.innerHTML = 'Save';
    }
}

// File Upload Handling
function setupDropzone(dropzoneId, inputId, handler) {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    
    if (!dropzone || !input) return;
    
    dropzone.addEventListener('click', () => input.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        handler(e.dataTransfer.files);
    });
    
    input.addEventListener('change', (e) => {
        handler(e.target.files);
    });
}

async function handleScriptUpload(files) {
    const file = files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(apiUrl('/api/upload/script'), {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            uploadedFiles.script = data;
            document.getElementById('script-info').classList.remove('hidden');
            document.getElementById('script-filename').textContent = data.filename;
            updateGenerateButtons();
            showNotification('Script uploaded successfully!', 'success');
        } else {
            showNotification('Failed to upload script', 'error');
        }
    } catch (error) {
        showNotification('Upload error: ' + error.message, 'error');
    }
}

async function handleVoiceUpload(files) {
    const file = files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(apiUrl('/api/upload/audio'), {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            uploadedFiles.voice = data;
            document.getElementById('voice-info').classList.remove('hidden');
            document.getElementById('voice-filename').textContent = data.filename;
            updateGenerateButtons();
            showNotification('Voiceover uploaded successfully!', 'success');
        } else {
            showNotification('Failed to upload voiceover', 'error');
        }
    } catch (error) {
        showNotification('Upload error: ' + error.message, 'error');
    }
}

async function handleBrollUpload(files) {
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('video_type', 'broll');
        
        try {
            const response = await fetch(apiUrl('/api/upload/video'), {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                uploadedFiles.brollClips.push(data);
                updateBrollList();
            }
        } catch (error) {
            console.error('Upload error:', error);
        }
    }
    
    updateOrganizeButton();
    showNotification(`Uploaded ${files.length} B-roll clips`, 'success');
}

async function handleIntroUpload(files) {
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('video_type', 'intro');
        
        try {
            const response = await fetch(apiUrl('/api/upload/video'), {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                uploadedFiles.introClips.push(data);
                updateIntroList();
            }
        } catch (error) {
            console.error('Upload error:', error);
        }
    }
    
    showNotification(`Uploaded ${files.length} intro clips`, 'success');
}

async function handleBrollVoiceUpload(files) {
    const file = files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(apiUrl('/api/upload/audio'), {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            uploadedFiles.brollVoice = data;
            document.getElementById('broll-voice-info').classList.remove('hidden');
            document.getElementById('broll-voice-filename').textContent = data.filename;
            showNotification('Voiceover uploaded successfully!', 'success');
        } else {
            showNotification('Failed to upload voiceover', 'error');
        }
    } catch (error) {
        showNotification('Upload error: ' + error.message, 'error');
    }
}

// UI Updates
function updateGenerateButtons() {
    const generateBtn = document.getElementById('generate-btn');
    const canGenerate = uploadedFiles.script && uploadedFiles.voice;
    generateBtn.disabled = !canGenerate;
}

function updateOrganizeButton() {
    const organizeBtn = document.getElementById('organize-btn');
    const canOrganize = uploadedFiles.brollClips.length > 0;
    organizeBtn.disabled = !canOrganize;
}

function updateBrollList() {
    const listEl = document.getElementById('broll-list');
    listEl.innerHTML = uploadedFiles.brollClips.map(clip => `
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span class="text-sm"><i class="fas fa-video mr-2"></i>${clip.filename}</span>
            <button class="text-red-500 hover:text-red-700" onclick="removeClip('broll', '${clip.file_id}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function updateIntroList() {
    const listEl = document.getElementById('intro-list');
    listEl.innerHTML = uploadedFiles.introClips.map(clip => `
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span class="text-sm"><i class="fas fa-film mr-2"></i>${clip.filename}</span>
            <button class="text-red-500 hover:text-red-700" onclick="removeClip('intro', '${clip.file_id}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeClip(type, fileId) {
    if (type === 'broll') {
        uploadedFiles.brollClips = uploadedFiles.brollClips.filter(c => c.file_id !== fileId);
        updateBrollList();
    } else {
        uploadedFiles.introClips = uploadedFiles.introClips.filter(c => c.file_id !== fileId);
        updateIntroList();
    }
    updateOrganizeButton();
}

// Job Processing
async function generateAIImages() {
    // Disable button to prevent multiple clicks
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Starting...';
    
    try {
        console.log('Starting image generation, reading script file...');
        console.log('Script file data:', uploadedFiles.script);
        
        // Try to read script content, but have a fallback
        let scriptText = await readScriptFile();
        if (!scriptText) {
            console.warn('Failed to read script file via API, using placeholder text');
            // Use a placeholder or prompt user to enter text
            scriptText = 'Generate images based on the uploaded script content.';
        }
        
        console.log('Preparing generation request...');
        const formData = new FormData();
        formData.append('script_file_id', uploadedFiles.script.file_id);
        formData.append('voice_file_id', uploadedFiles.voice.file_id);
        formData.append('script_text', scriptText);
        formData.append('image_count', document.getElementById('image-count').value);
        formData.append('style', document.getElementById('image-style').value);
        formData.append('character_description', document.getElementById('character-desc').value || 'High quality visuals');
        formData.append('voice_duration', '60'); // Will be calculated server-side
        formData.append('export_options', JSON.stringify({
            images: document.getElementById('export-images').checked,
            clips: document.getElementById('export-clips').checked,
            full_video: document.getElementById('export-full-video').checked
        }));
        
        console.log('Sending generation request...');
        const response = await fetch(apiUrl('/api/generate/ai-images'), {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Generation started:', data);
            showNotification('AI image generation started!', 'success');
            
            // Show progress section
            document.getElementById('ai-progress-section').classList.remove('hidden');
            
            // Start tracking the job
            trackJob(data.job_id, 'ai');
        } else {
            let errorMessage = 'Failed to start generation';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                errorMessage = await response.text() || errorMessage;
            }
            console.error('Generation error:', errorMessage);
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Error in generateAIImages:', error);
        showNotification('Error: ' + error.message, 'error');
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Generate AI Images';
        updateGenerateButtons();
    }
}

async function organizeBroll() {
    console.log('🎬 organizeBroll function called');
    
    // Check if we have B-roll clips
    if (uploadedFiles.brollClips.length === 0) {
        showNotification('Please upload at least one B-roll clip first', 'error');
        return;
    }
    
    // Show starting popup modal
    const startingModal = document.getElementById('progress-starting-modal');
    const startingProgressBar = document.getElementById('starting-progress-bar');
    const startingStatus = document.getElementById('starting-status');
    
    startingModal.classList.remove('hidden');
    startingProgressBar.style.width = '0%';
    startingStatus.textContent = 'Initializing...';
    
    // Animate the starting popup progress
    setTimeout(() => {
        startingProgressBar.style.width = '20%';
        startingStatus.textContent = 'Validating uploaded files...';
    }, 300);
    
    setTimeout(() => {
        startingProgressBar.style.width = '50%';
        startingStatus.textContent = 'Preparing server request...';
    }, 600);
    
    setTimeout(() => {
        startingProgressBar.style.width = '80%';
        startingStatus.textContent = 'Starting processing...';
    }, 900);
    
    // Show progress section immediately
    const progressSection = document.getElementById('broll-progress-section');
    const progressBar = document.getElementById('broll-progress-bar');
    const progressPercent = document.getElementById('broll-progress-percent');
    const statusEl = document.getElementById('broll-status');
    
    progressSection.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressPercent.textContent = '0';
    statusEl.textContent = 'Initializing B-roll organization...';
    
    // Reset progress bar colors
    resetProgressBar('broll');
    
    // Disable button to prevent multiple clicks
    const organizeBtn = document.getElementById('organize-btn');
    organizeBtn.disabled = true;
    organizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Starting...';
    
    const requestData = {
        intro_clip_ids: uploadedFiles.introClips.map(c => c.file_id),
        broll_clip_ids: uploadedFiles.brollClips.map(c => c.file_id),
        voiceover_id: uploadedFiles.brollVoice?.file_id || null,
        sync_to_voiceover: document.getElementById('sync-duration').checked,
        overlay_audio: document.getElementById('overlay-audio').checked
    };
    
    console.log('📋 Request data:', requestData);
    console.log('📁 Uploaded files:', uploadedFiles);
    
    try {
        // Update progress to show we're sending request
        progressBar.style.width = '5%';
        progressPercent.textContent = '5';
        statusEl.textContent = 'Sending request to server...';
        
        console.log('Starting B-roll organization with data:', requestData);
        console.log('Sending POST request to', apiUrl('/api/generate/broll'));
        
        const response = await fetch(apiUrl('/api/generate/broll'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ B-roll organization started successfully:', data);
            
            // Complete the starting popup animation
            startingProgressBar.style.width = '100%';
            startingStatus.textContent = 'Job started successfully!';
            
            // Close the starting modal after a brief moment
            setTimeout(() => {
                startingModal.classList.add('hidden');
            }, 800);
            
            showNotification('B-roll organization started!', 'success');
            
            // Update progress to show job started
            progressBar.style.width = '10%';
            progressPercent.textContent = '10';
            statusEl.textContent = 'Job queued successfully. Processing...';
            
            trackJob(data.job_id, 'broll');
        } else {
            console.error('❌ Server returned error status:', response.status);
            let errorMessage = 'Failed to start organization';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
                console.error('Error details:', error);
            } catch (e) {
                console.error('Failed to parse error response as JSON');
                errorMessage = await response.text() || errorMessage;
            }
            console.error('Organization error:', errorMessage);
            showNotification(errorMessage, 'error');
            
            // Close the starting modal on error
            startingModal.classList.add('hidden');
            
            // Hide progress section on error
            progressSection.classList.add('hidden');
        }
    } catch (error) {
        console.error('❌ Network or JavaScript error in organizeBroll:', error);
        console.error('Error type:', error.constructor.name);
        console.error('Error stack:', error.stack);
        showNotification('Error: ' + error.message, 'error');
        
        // Close the starting modal on error
        startingModal.classList.add('hidden');
        
        // Hide progress section on error
        progressSection.classList.add('hidden');
    } finally {
        // Re-enable button
        organizeBtn.disabled = false;
        organizeBtn.innerHTML = '<i class="fas fa-random mr-2"></i>Reorganize B-Roll';
        updateOrganizeButton();
    }
}

async function readScriptFile() {
    if (!uploadedFiles.script) {
        return null;
    }
    
    try {
        // Read the script file content
        const response = await fetch(apiUrl(`/api/files/${uploadedFiles.script.file_id}/content`));
        if (response.ok) {
            const data = await response.json();
            const content = data.content;
            console.log('Script content read successfully:', content.substring(0, 100) + '...');
            return content;
        } else {
            console.error('Failed to read script file:', response.status, response.statusText);
            try {
                const errorData = await response.json();
                console.error('Error details:', errorData);
            } catch (e) {
                // Ignore JSON parse errors
            }
            return null;
        }
    } catch (error) {
        console.error('Error reading script file:', error);
        return null;
    }
}

function trackJob(jobId, type) {
    const progressSection = document.getElementById(`${type}-progress-section`);
    const progressBar = document.getElementById(`${type}-progress-bar`);
    const progressPercent = document.getElementById(`${type}-progress-percent`);
    const statusEl = document.getElementById(`${type}-status`);
    
    progressSection.classList.remove('hidden');
    
    // Add a small delay to show the initial progress
    setTimeout(() => {
        progressBar.style.width = '15%';
        progressPercent.textContent = '15';
        statusEl.textContent = 'Checking job status...';
    }, 500);
    
    // Poll for job status
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(apiUrl(`/api/jobs/${jobId}`));
            
            if (response.ok) {
                const job = await response.json();
                
                // Update progress with smooth animation
                progressBar.style.width = `${job.progress}%`;
                progressPercent.textContent = job.progress;
                
                // Enhance status message with more detail
                let statusMessage = job.message || 'Processing...';
                if (job.progress > 0 && job.progress < 100) {
                    statusMessage = `${statusMessage} (${job.progress}% complete)`;
                }
                statusEl.textContent = statusMessage;
                
                // Add visual feedback for different stages
                if (job.progress >= 50) {
                    progressBar.classList.add('bg-blue-600');
                    progressBar.classList.remove('bg-green-600');
                }
                if (job.progress >= 90) {
                    progressBar.classList.add('bg-purple-600');
                    progressBar.classList.remove('bg-blue-600');
                }
                
                if (job.status === 'completed') {
                    clearInterval(pollInterval);
                    
                    // Final progress update
                    progressBar.style.width = '100%';
                    progressPercent.textContent = '100';
                    progressBar.classList.add('bg-green-600');
                    progressBar.classList.remove('bg-purple-600', 'bg-blue-600');
                    statusEl.textContent = '🎉 B-roll organization completed successfully!';
                    
                    showNotification('B-roll organization completed successfully! <a href="results.html" class="underline font-semibold">View Results</a>', 'success');
                    
                    // Handle different job types
                    if (type === 'ai' && job.result) {
                        displayGeneratedImages(job.result);
                    }
                    
                    if (type === 'broll' && job.result_url) {
                        showDownloadLink(job.result_url, 'broll');
                    }
                    
                    if (job.result_url) {
                        showDownloadLink(job.result_url, type);
                    }
                    
                    // Auto-hide progress after 5 seconds
                    setTimeout(() => {
                        progressSection.classList.add('hidden');
                    }, 5000);
                    
                } else if (job.status === 'failed') {
                    clearInterval(pollInterval);
                    
                    // Show error state
                    progressBar.classList.add('bg-red-600');
                    progressBar.classList.remove('bg-green-600', 'bg-blue-600', 'bg-purple-600');
                    statusEl.textContent = `❌ Failed: ${job.message}`;
                    
                    showNotification('Job failed: ' + job.message, 'error');
                    console.error('Job failed:', job);
                    
                    // Auto-hide progress after 10 seconds
                    setTimeout(() => {
                        progressSection.classList.add('hidden');
                    }, 10000);
                }
            } else {
                console.error('Failed to get job status:', response.status);
                statusEl.textContent = '⚠️ Unable to get job status. Retrying...';
            }
        } catch (error) {
            console.error('Failed to poll job status:', error);
            statusEl.textContent = '⚠️ Connection error. Retrying...';
        }
    }, 2000);
}

function displayGeneratedImages(result) {
    // Show preview section
    const previewSection = document.getElementById('ai-preview-section');
    const previewGrid = document.getElementById('ai-preview-grid');
    
    if (result && result.images && result.images.length > 0) {
        previewSection.classList.remove('hidden');
        
        // Clear existing previews
        previewGrid.innerHTML = '';
        
        // Add image previews
        result.images.forEach((imagePath, index) => {
            const imageDiv = document.createElement('div');
            imageDiv.className = 'relative group';
            imageDiv.innerHTML = `
                <img src="${apiUrl(`/api/files/serve/${imagePath}`)}" alt="Generated Image ${index + 1}" 
                     class="w-full h-48 object-cover rounded-lg shadow-md hover:shadow-xl transition-shadow">
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity rounded-lg flex items-center justify-center">
                    <a href="${apiUrl(`/api/files/serve/${imagePath}`)}" download 
                       class="opacity-0 group-hover:opacity-100 transition-opacity bg-white px-3 py-1 rounded text-sm">
                        <i class="fas fa-download mr-1"></i>Download
                    </a>
                </div>
            `;
            previewGrid.appendChild(imageDiv);
        });
    }
}

function showDownloadLink(url, type) {
    const link = document.createElement('a');
    link.href = url;
    link.className = 'inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700';
    link.innerHTML = '<i class="fas fa-download mr-2"></i>Download Result';
    link.download = true;
    
    const progressSection = document.getElementById(`${type}-progress-section`);
    progressSection.appendChild(link);
}

function resetProgressBar(type) {
    const progressBar = document.getElementById(`${type}-progress-bar`);
    if (progressBar) {
        progressBar.classList.remove('bg-red-600', 'bg-blue-600', 'bg-purple-600');
        progressBar.classList.add('bg-green-600');
    }
}

// Jobs Management
async function loadJobs() {
    try {
        const response = await fetch(apiUrl('/api/jobs'));
        
        if (response.ok) {
            const jobs = await response.json();
            displayJobs(jobs);
        }
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
}

function displayJobs(jobs) {
    const jobsList = document.getElementById('jobs-list');
    
    if (jobs.length === 0) {
        jobsList.innerHTML = '<p class="text-gray-500">No jobs found</p>';
        return;
    }
    
    jobsList.innerHTML = jobs.map(job => `
        <div class="border rounded-lg p-4">
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-semibold">${job.job_type === 'ai_image_generation' ? 'AI Image Generation' : 'B-Roll Organization'}</h4>
                    <p class="text-sm text-gray-600">${new Date(job.created_at).toLocaleString()}</p>
                    <p class="text-sm mt-2">Status: <span class="font-semibold ${getStatusColor(job.status)}">${job.status}</span></p>
                    ${job.message ? `<p class="text-sm text-gray-600">${job.message}</p>` : ''}
                </div>
                <div class="flex space-x-2">
                    ${job.result_url ? `<a href="${job.result_url}" class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700" download><i class="fas fa-download mr-1"></i>Download</a>` : ''}
                    ${job.status === 'processing' || job.status === 'pending' ? `<button class="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700" onclick="cancelJob('${job.job_id}')"><i class="fas fa-times mr-1"></i>Cancel</button>` : ''}
                </div>
            </div>
            ${job.progress > 0 ? `
                <div class="mt-3">
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" style="width: ${job.progress}%"></div>
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function getStatusColor(status) {
    const colors = {
        'pending': 'text-yellow-600',
        'processing': 'text-blue-600',
        'completed': 'text-green-600',
        'failed': 'text-red-600',
        'cancelled': 'text-gray-600'
    };
    return colors[status] || 'text-gray-600';
}

async function cancelJob(jobId) {
    if (!confirm('Are you sure you want to cancel this job?')) return;
    
    try {
        const response = await fetch(apiUrl(`/api/jobs/${jobId}`), {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Job cancelled', 'info');
            loadJobs();
        }
    } catch (error) {
        showNotification('Failed to cancel job', 'error');
    }
}

// WebSocket for real-time updates
function connectWebSocket() {
    // No authentication needed for public app
    const wsHost = API_BASE_URL.replace('http://', '').replace('https://', '');
    const wsUrl = `ws://${wsHost}/ws/public`; // Assuming a public endpoint for WebSocket
    ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleJobUpdate(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };
}

function handleJobUpdate(data) {
    // Update progress if tracking this job
    const progressBar = document.querySelector(`[data-job-id="${data.job_id}"]`);
    if (progressBar) {
        progressBar.style.width = `${data.progress}%`;
    }
    
    // Refresh jobs list if on jobs tab
    if (document.getElementById('jobs').classList.contains('active')) {
        loadJobs();
    }
}

// Utility functions
function showModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function showNotification(message, type = 'info') {
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white ${colors[type]} shadow-lg z-50`;
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Make closeModal available globally
window.closeModal = closeModal;