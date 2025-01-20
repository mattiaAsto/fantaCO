document.addEventListener("DOMContentLoaded", () => {
  const icon_eye = "fas fa-eye";
  const icon_eye_slash = "fas fa-eye-slash";

  /*   const right_div = document.querySelector(".header-right-section");
  const header_links = document.querySelectorAll(".header-link");
  const header = document.querySelector("header");

  right_div.addEventListener("click", () => {
    header_links.forEach((link) => {
      link.classList.toggle("active");
    });
  });

  document.addEventListener("click", (e) => {
    if (!header.contains(e.target)) {
      // Controlla se il clic è fuori dal nav
      header_links.forEach((link) => {
        link.classList.toggle("active");
      });
    }
  });

  const header_bars = document.querySelector(".header-bars");
  const nav_links = document.querySelectorAll("nav");

  header_bars.addEventListener("click", () => {
    nav_links.forEach((link) => {
      link.classList.toggle("active");
    });
  });

  document.addEventListener("click", (e) => {
    if (!header.contains(e.target)) {
      // Controlla se il clic è fuori dal nav
      nav_links.forEach((link) => {
        link.classList.toggle("active");
      });
    }
  }); */

  const password_field1 = document.querySelector("#password1");
  const password_field2 = document.querySelector("#password2");
  const eye_button1 = document.querySelector("#eye1");
  const eye_button2 = document.querySelector("#eye2");
  console.log("ciao");

  eye_button1.addEventListener("click", () => {
    if (password_field1.type === "password") {
      password_field1.type = "text";
      eye_button1.classList = icon_eye;
    } else {
      password_field1.type = "password";
      eye_button1.classList = icon_eye_slash;
    }
  });

  eye_button2.addEventListener("click", () => {
    if (password_field2.type === "password") {
      password_field2.type = "text";
      eye_button2.classList = icon_eye;
    } else {
      password_field2.type = "password";
      eye_button2.classList = icon_eye_slash;
    }
  });

  document
    .getElementById("register-form")
    .addEventListener("submit", function (event) {
      event.preventDefault(); // Preveniamo il comportamento di submit normale

      var username = document.getElementById("username").value
      var password = document.getElementById("password1").value;
      var password2 = document.getElementById("password2").value;
      console.log(password, password2)

      var formData = new FormData();
      formData.append("username", username)
      formData.append("password1", password);
      formData.append("password2", password2);

      fetch("/auth/validate_registration", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            document.getElementById("error-message").innerText = data.error;
          } else {
            document.getElementById("error-message").innerText = ""; // Rimuovi il messaggio di errore
            document.getElementById('register-form').submit();
          };
        })
        .catch((error) => console.error("Error:", error));
    });
});
