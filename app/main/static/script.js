
function swap_league() {
	const overlay = document.querySelector(".leagues_overlay");
	const popup = document.querySelector(".leagues_popup");

	const popup_league_form = document.querySelectorAll("#league-form");

	overlay.classList.add("active");
	popup.classList.add("active");
	document.body.classList.add("no-scroll");

	popup_league_form.forEach(form => {
		form.addEventListener("click", function(event) {
			
			fetch(form.action, {
				method: form.method,
				body: new FormData(form)
			})
			.then(response => {
				if (response.ok) {
					window.location.reload();
				} else {
					throw new Error("Errore nell'invio del form");
				}
			})
			.catch(error => {
				console.error("Errore durante l'invio del form:", error);
			});
		});
		
	});
}

//show popup for chosing the selling runner
function show_sell_popup() {
	const overlay = document.querySelector(".sell-overlay");
	const popup = document.querySelector(".sell-popup");
	overlay.classList.add("active");
	popup.classList.add("active");
	document.body.classList.add("no-scroll");

	return;
}


document.addEventListener("DOMContentLoaded", () => {
	//FUNCTIONS

    //side scrolling of main content
    function main_side_scroll(index) {
        const slideWidth = document.querySelector(".main-slider").offsetWidth;
		lineup_slider = document.querySelector(".main-slides");
		lineup_slider.style.transform = `translateX(-${index * slideWidth}px)`;
	}

    //side scrolling of lineups
	function lineup_side_scroll(index) {
		const lineup_width = document.querySelector(".lineup-slide").offsetWidth;
		lineup_slider = document.querySelector(".lineup-slider");
		lineup_slider.style.transform = `translateX(-${index * lineup_width}px)`;
	}

    //show popup for chosing linups
    function show_lineup_popup(i) {
		const overlay = document.querySelector(".lineup-overlay");
		const popup = document.querySelector(".lineup-popup");
		overlay.classList.add("active");
		popup.classList.add("active");
		document.body.classList.add("no-scroll");

		const forms = document.querySelectorAll("#popup-runner-form");
		console.log(forms)

		forms.forEach((form) => {
			const inputNumber = form.querySelector('input[name="number"]');
			if (inputNumber) {
				inputNumber.value = i;
			}
		});
		return;
	}

    //hide popup for chosing lineups
	function hide_popup() {
		const overlays = document.querySelectorAll(".overlay");
		const popups = document.querySelectorAll(".popup");

		overlays.forEach(overlay => {
			overlay.classList.remove("active");
		});
		popups.forEach(popup => {
			popup.classList.remove("active");
		});
		document.body.classList.remove("no-scroll");
		return;
	}

	//add the popup behavior to the add runner buttons in lineups
	function lineup_runnner_button_add_function() {
		const lineup_button = document.querySelectorAll(".lineup-runner-button");
		if (lineup_button.length) {
			lineup_button.forEach((button, i) => {
				button.addEventListener("click", () => {
					show_lineup_popup(i + 1);
				});
			});
		} else {
			console.error(
				"Bottoni nella classe '.lineup-runner-button' non trovati."
			);
		}
	}

	//refresh just part of the lineup page without refreshing the whole page, this keeps the user experience fluid and dynamic
	function reload_lineup() {
		fetch("/team")
			.then((response) => response.text())
			.then((data) => {

				const parser = new DOMParser();
				const doc = parser.parseFromString(data, "text/html");
				const new_content = doc.querySelector(".lineup-slider"); 
				console.log(new_content);

				document.querySelector(".lineup-slider").innerHTML = new_content.innerHTML;

				lineup_runnner_button_add_function();
			})
			.catch((error) => console.error("Errore:", error));
	}

	//refresh part of the sell page without whole refresh
	function reload_sellpage() {
		fetch("/market")
			.then((response) => response.text())
			.then((data) => {

				const parser = new DOMParser();
				const doc = parser.parseFromString(data, "text/html");
				const new_content = doc.getElementById("sell-runner");

				document.getElementById("sell-runner").innerHTML = new_content.innerHTML;

			})
			.catch((error) => console.error("Errore:", error));
	}
	
	//add closing popup behaviour
	function add_close_popup_behaviour(){
		const popup_x = document.querySelectorAll("#popup-x");

		popup_x.forEach(x => {
			x.addEventListener("click", () =>{
				hide_popup();
			});	
		});
	}

	//DOM content loaded actions

	//create the header links toggle effect for mobiles
	const right_div = document.querySelector(".header-right-section");
	const header_links = document.querySelectorAll(".header-link");
	right_div.addEventListener("click", () => {
		header_links.forEach((link) => {
			link.classList.toggle("active");
		});
	});

	//create navbar show/hide effect
	const header_bars = document.querySelector(".header-bars");
	const nav_links = document.querySelectorAll("nav");
	const bars = document.querySelector("#bars");
	header_bars.addEventListener("click", () => {
		nav_links.forEach((link) => {
			link.classList.toggle("active");
		});
		if (bars.classList.contains("fa-bars")) {
			console.log("entered");
			bars.classList = "fas fa-x bars-icon";
		} else {
			bars.classList = "fas fa-bars bars-icon";
		}
	});

	//create the sidesceroll effect for
	const choice_divs = document.querySelectorAll(".choice-div");
	if (choice_divs.length) {
		choice_divs.forEach((choice, i) => {
			choice.addEventListener("click", () => {
				console.log("done");
				choice_divs.forEach((btn) => btn.classList.remove("active"));
				choice.classList.add("active");

				main_side_scroll(i);
			});
		});
	} else {
		console.error("Bottoni nella classe '.options' non trovati.");
	}

	//create the sidescroll effect for lineups
	const buttons = document.querySelectorAll(".lineup-selection-button");
	if (buttons.length) {
		buttons.forEach((button, i) => {
			button.addEventListener("click", () => {
				buttons.forEach((btn) => btn.classList.remove("active"));
				button.classList.add("active");

				lineup_side_scroll(i);
			});
		});
	} else {
		console.error("Bottoni nella classe '.options' non trovati.");
	}

	//call the function, for more infos read function comment
	lineup_runnner_button_add_function();
	
	//behavior when new lineup runner is selected, fetch main.refresh_team and then reload part of the content on the page without refresh
	const popup_lineup_div = document.querySelectorAll("#lineup-div");
	if (popup_lineup_div.length) {
		popup_lineup_div.forEach((div, i) => {
			div.addEventListener("click", function (event) {
				var form = div.querySelector("form")
				console.log(form)
				const formData = new FormData(form);
				console.log(form.action)

				fetch(form.action, {
					method: form.method,
					body: formData,
				})
					.then((response) => response.json())
					.then((data) => {
						reload_lineup();
						hide_popup();
					})
					.catch((error) => {
						console.error("Errore:", error);
					});
			});
		});
	} else {
		console.error(
			"Bottoni nella classe '.lineup-runner-button' non trovati."
		);
	}

	/* const popup_sell_div = document.querySelectorAll("#sell-div");
	if (popup_sell_div.length) {
		popup_sell_div.forEach((div, i) => {
			div.addEventListener("click", function (event) {
				var form = div.querySelector("form")
				console.log(form)
				const formData = new FormData(form);
				console.log(form.action)

				fetch(form.action, {
					method: form.method,
					body: formData,
				})
					.then((response) => response.json())
					.then((data) => {
						hide_popup();
						reload_sellpage();
					})
					.catch((error) => {
						console.error("Errore:", error);
					});
			});
		});
	} else {
		console.error(
			"Bottoni nella classe '.lineup-runner-button' non trovati."
		);
	}
 */
	//add the close the popup with x icon
	add_close_popup_behaviour();


	const leave_league_form = document.querySelectorAll(".leave-league-form");
	leave_league_form.forEach((form) => {
		form.addEventListener("click", function (event) {
			if (confirm("Sei sicuro di voler abbandonare la lega?")) {
				form.submit();
			};
		});
	});

	const scrollContainer = document.querySelector(".orunner-points-display");
	console.log(scrollContainer);
    scrollContainer.addEventListener("wheel", (event) => {
        event.preventDefault(); // Evita lo scroll verticale della pagina
        scrollContainer.scrollLeft -= (event.deltaY)*0.3; // Converte lo scroll verticale in orizzontale
    });
	









	/* document.addEventListener("click", (e) => {
    if (!header.contains(e.target)) {
      // Controlla se il clic è fuori dal nav
      nav_links.forEach((link) => {
        link.classList.toggle("active");
      });
    }
  }); */
});
