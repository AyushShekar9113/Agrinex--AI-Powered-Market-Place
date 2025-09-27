// Toggle sidebar open/close
document.getElementById('hamburger').addEventListener('click', function () {
    toggleSidebar();
});

// Function to toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    // Use getComputedStyle to check the actual width of the sidebar
    const sidebarWidth = window.getComputedStyle(sidebar).width;

    if (sidebarWidth === '250px') {  // Compare the actual width
        sidebar.style.width = '0';
        mainContent.classList.remove('active');
    } else {
        sidebar.style.width = '250px';
        mainContent.classList.add('active');
    }
}

// Handle sidebar button clicks
const sidebarButtons = document.querySelectorAll('.sidebar-btn');  // Use .sidebar-btn for all sidebar buttons

sidebarButtons.forEach(button => {
    button.addEventListener('click', function () {
        // Remove active class from all buttons
        sidebarButtons.forEach(btn => btn.classList.remove('active'));

        // Optional: Auto-close sidebar after clicking (better UX on mobile)
        closeSidebar();
    });
});

// Function to close sidebar (optional for smoother UX)
function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    sidebar.style.width = '0';  // Close sidebar
    mainContent.classList.remove('active');  // Remove active class from main content
}

// Function to navigate to the weather page
function navigateToWeather() {
    window.location.href = "{{ url_for('weather') }}";  // Flask correct URL
}

// Optional: Add event listener to dynamically update the active state of the buttons
document.querySelectorAll('.sidebar-btn').forEach(button => {
    button.addEventListener('click', function() {
        // Set the clicked button as active
        this.classList.add('active');
    });
});
