
// Function to show a specific page
function showPage(pageIndex) {
    // Hide all pages
    const pages = document.querySelectorAll('.page-container');
    pages.forEach(page => {
        page.style.display = 'none';
    });
    
    // Show the selected page
    const selectedPage = document.getElementById(`page-${pageIndex}`);
    if (selectedPage) {
        selectedPage.style.display = 'block';
    }
    
    // Update navigation buttons
    const buttons = document.querySelectorAll('.page-nav-btn');
    buttons.forEach((btn, idx) => {
        if (idx === pageIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Function to show a specific tab
function showTab(pageIndex, tabName) {
    // Hide all tabs for this page
    const tabs = document.querySelectorAll(`#page-${pageIndex} .tab-pane`);
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show the selected tab
    const selectedTab = document.getElementById(`page-${pageIndex}-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Update tab buttons
    const buttons = document.querySelectorAll(`#page-${pageIndex} .tab-btn`);
    buttons.forEach(btn => {
        if (btn.innerText.toLowerCase() === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Initialize tooltips for text blocks, tables, and figures
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here
});
