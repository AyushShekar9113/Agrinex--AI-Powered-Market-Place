// Background images for each role
const bgMap = {
  farmer: "/static/images/farmer.png",
  buyer: "/static/images/buyer.png",
  admin: "/static/images/admin.png"
};

// Role selection and background change
function selectRole(role) {
  const sections = ["farmer", "buyer", "admin", "buyer-signup"];

  // Hide all sections
  sections.forEach(section => {
    const sec = document.getElementById(`${section}-section`);
    if (sec) {
      sec.style.display = "none";
    }
  });

  const signupSection = document.getElementById("buyer-signup-section");
  if (signupSection) signupSection.style.display = "none";

  // Show the selected section
  const selectedSection = document.getElementById(`${role}-section`);
  if (selectedSection) {
    selectedSection.style.display = "block";
  }

  // Change background image based on the selected role
  if (bgMap[role]) {
    document.body.style.backgroundImage = `url('${bgMap[role]}')`;
  }

  // Scroll to the login area smoothly
  scrollToLogin();
}

// Scroll to login area smoothly
function scrollToLogin() {
  const loginArea = document.getElementById("login-area");
  if (loginArea) {
    loginArea.scrollIntoView({ behavior: "smooth" });
  }
}

// Show buyer signup form
function showSignup() {
  const buyerSection = document.getElementById("buyer-section");
  const signupSection = document.getElementById("buyer-signup-section");

  if (buyerSection) buyerSection.style.display = "none";
  if (signupSection) signupSection.style.display = "block";
}

// Handle Farmer login submit
function loginFarmer(event) {
  event.preventDefault();

  const form = document.getElementById("farmerLoginForm");
  const formData = new FormData(form);

  fetch("/login/farmer", {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    const msg = document.getElementById("farmerLoginMsg");
    if (data.status === "success") {
      msg.style.color = "green";
      msg.textContent = `Welcome, ${data.data.name || 'Farmer'}! 🌾`;
      setTimeout(() => {
        window.location.href = "/home"; 
      }, 1000); // 1 second delay
    } else {
      msg.style.color = "red";
      msg.textContent = data.message;
    }
  })
  .catch(error => {
    console.error("Error:", error);
  });
}

// Handle Buyer login submit
function loginBuyer(event) {
  event.preventDefault();

  const form = document.getElementById("buyerLoginForm");
  const formData = new FormData(form);

  fetch("/login/buyer", {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    const msg = document.getElementById("buyerLoginMsg");
    if (data.status === "success") {
      msg.style.color = "green";
      msg.textContent = `Welcome, ${data.name}! 🎉`;
      setTimeout(() => {
        window.location.href = "/home"; 
      }, 1000); // 1 second delay
    } else {
      msg.style.color = "red";
      msg.textContent = data.message;
    }
  })
  .catch(error => {
    console.error("Error:", error);
  });
}

// Handle Buyer signup submit
function signupBuyer(event) {
  event.preventDefault();

  const form = document.getElementById("buyerSignupForm");
  const formData = new FormData(form);

  fetch("/signup/buyer", {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    const msg = document.getElementById("buyerSignupMsg");
    if (data.status === "success") {
      msg.style.color = "green";
      msg.textContent = data.message;
      form.reset();
    } else {
      msg.style.color = "red";
      msg.textContent = data.message;
    }
  })
  .catch(error => {
    console.error("Error:", error);
  });
}
function loginAdmin(e) {
  e.preventDefault();  // Prevent form from submitting normally

  const adminId = document.getElementById('adminId').value;
  const password = document.getElementById('adminPassword').value;

  fetch('/login/admin', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      adminid: adminId,
      password: password,
    }),
  })
  .then(response => {
    if (response.redirected) {
      // If the response is a redirect, follow it automatically
      window.location.href = response.url;
    } else {
      document.getElementById('adminLoginMsg').textContent = 'Login failed!';
      document.getElementById('adminLoginMsg').style.color = 'red';
    }
  })
  .catch(error => {
    console.error('Error during login:', error);
    document.getElementById('adminLoginMsg').textContent = 'An error occurred, please try again later.';
    document.getElementById('adminLoginMsg').style.color = 'red';
  });
}

// DOMContentLoaded - attach everything
document.addEventListener("DOMContentLoaded", function() {
  // Fade-in animation for login wrapper
  const wrapper = document.getElementById("loginWrapper");
  if (wrapper) {
    wrapper.classList.add("show");
  }

  // Role buttons click event
  const roleButtons = document.querySelectorAll('.role-button');
  roleButtons.forEach(button => {
    button.addEventListener('click', function() {
      const role = this.dataset.role;
      if (role) {
        selectRole(role);
      }
    });
  });

  // Attach form listeners
  const farmerLoginForm = document.getElementById("farmerLoginForm");
  if (farmerLoginForm) farmerLoginForm.addEventListener("submit", loginFarmer);

  const buyerLoginForm = document.getElementById("buyerLoginForm");
  if (buyerLoginForm) buyerLoginForm.addEventListener("submit", loginBuyer);

  const buyerSignupForm = document.getElementById("buyerSignupForm");
  if (buyerSignupForm) buyerSignupForm.addEventListener("submit", signupBuyer);

  const adminLoginForm = document.getElementById("adminLoginForm");
  if (adminLoginForm) adminLoginForm.addEventListener("submit", loginAdmin);
});