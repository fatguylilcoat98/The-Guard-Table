// Research Section JavaScript
function toggleResearch() {
    const content = document.getElementById('research-content');
    const button = document.querySelector('.research-toggle');
    const toggleText = button.querySelector('.toggle-text');

    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        button.classList.add('collapsed');
        toggleText.textContent = 'View Research';
    } else {
        content.classList.add('expanded');
        button.classList.remove('collapsed');
        toggleText.textContent = 'Hide Research';
    }
}

function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked button
    const clickedButton = event ? event.target : document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
}

// Smooth scroll to research section when navigation link is clicked
function scrollToResearch() {
    const researchSection = document.getElementById('research-section');
    if (researchSection) {
        researchSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Add click handler to research navigation link
document.addEventListener('DOMContentLoaded', function() {
    const researchNavLink = document.querySelector('a[href="#research-section"]');
    if (researchNavLink) {
        researchNavLink.addEventListener('click', function(e) {
            e.preventDefault();
            scrollToResearch();
        });
    }
});