// Main JavaScript for CleanConnect

document.addEventListener('DOMContentLoaded', function() {
    // Form step navigation
    setupFormSteps();
    
    // Job Type Toggle
    setupJobTypeToggle();
    
    // Work Hours Chart
    setupWorkHoursChart();
    
    // Time Tracking
    setupTimeTracking();
});

// Multi-step form navigation
function setupFormSteps() {
    const nextButtons = document.querySelectorAll('.next-step');
    const prevButtons = document.querySelectorAll('.prev-step');
    
    if (nextButtons.length) {
        nextButtons.forEach(button => {
            button.addEventListener('click', function() {
                const currentStep = parseInt(this.getAttribute('data-step'));
                const nextStep = currentStep + 1;
                
                // Validate current step
                if (!validateStep(currentStep)) {
                    return;
                }
                
                // Hide current step
                document.getElementById(`step-content-${currentStep}`).classList.add('d-none');
                
                // Show next step
                document.getElementById(`step-content-${nextStep}`).classList.remove('d-none');
                
                // Update progress indicator
                document.getElementById(`step-${currentStep}`).classList.remove('active');
                document.getElementById(`step-${nextStep}`).classList.add('active');
            });
        });
    }
    
    if (prevButtons.length) {
        prevButtons.forEach(button => {
            button.addEventListener('click', function() {
                const currentStep = parseInt(this.getAttribute('data-step'));
                const prevStep = currentStep - 1;
                
                // Hide current step
                document.getElementById(`step-content-${currentStep}`).classList.add('d-none');
                
                // Show previous step
                document.getElementById(`step-content-${prevStep}`).classList.remove('d-none');
                
                // Update progress indicator
                document.getElementById(`step-${currentStep}`).classList.remove('active');
                document.getElementById(`step-${prevStep}`).classList.add('active');
            });
        });
    }
}

// Job Type field toggles
function setupJobTypeToggle() {
    const jobTypeSelect = document.getElementById('id_job_type');
    
    if (jobTypeSelect) {
        jobTypeSelect.addEventListener('change', function() {
            const jobType = this.value;
            const oneTimeFields = document.getElementById('one-time-fields');
            const recurringFields = document.getElementById('recurring-fields');
            const contractFields = document.getElementById('contract-fields');
            
            // Hide all first
            if (oneTimeFields) oneTimeFields.classList.add('d-none');
            if (recurringFields) recurringFields.classList.add('d-none');
            if (contractFields) contractFields.classList.add('d-none');
            
            // Show relevant fields
            if (jobType === 'one_time' && oneTimeFields) {
                oneTimeFields.classList.remove('d-none');
            } else if (jobType === 'recurring') {
                if (oneTimeFields) oneTimeFields.classList.remove('d-none');
                if (recurringFields) recurringFields.classList.remove('d-none');
            } else if (jobType === 'contract') {
                if (oneTimeFields) oneTimeFields.classList.remove('d-none');
                if (contractFields) contractFields.classList.remove('d-none');
            }
        });
        
        // Trigger on load
        jobTypeSelect.dispatchEvent(new Event('change'));
    }
}

// Validate form steps
function validateStep(step) {
    // This is a simple implementation, you might want to expand with actual validation
    return true;
}

// Work Hours Chart
function setupWorkHoursChart() {
    const chartCanvas = document.getElementById('workHoursChart');
    
    if (chartCanvas) {
        // Sample data - this would be populated from the backend
        const ctx = chartCanvas.getContext('2d');
        const workHoursChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Hours Worked',
                    data: [6, 8, 5, 7, 4, 0, 0],
                    backgroundColor: '#0052CC',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            stepSize: 2
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Time Tracking
function setupTimeTracking() {
    const timeElapsed = document.getElementById('timeElapsed');
    const clockInBtn = document.getElementById('clockInBtn');
    
    if (timeElapsed) {
        // Calculate time elapsed since clock in
        const clockInTime = new Date(timeElapsed.getAttribute('data-clock-in') || new Date());
        
        // Update the timer every second
        setInterval(() => {
            const now = new Date();
            const elapsed = Math.floor((now - clockInTime) / 1000);
            
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            timeElapsed.textContent = 
                (hours < 10 ? '0' + hours : hours) + ':' +
                (minutes < 10 ? '0' + minutes : minutes) + ':' +
                (seconds < 10 ? '0' + seconds : seconds);
        }, 1000);
    }
    
    if (clockInBtn) {
        // Capture location when clocking in
        clockInBtn.addEventListener('click', function(e) {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    document.getElementById('lat').value = position.coords.latitude;
                    document.getElementById('lng').value = position.coords.longitude;
                }, function(error) {
                    console.error("Error getting location", error);
                });
            }
        });
    }
}