const selectButton = document.getElementById("select-button");
const selectList = document.getElementById("option-list");

selectButton.addEventListener("click", function() {
	optionList.classList.toggle("hidden");
});

optionList.addEventListener("click", function (event) {
	if (event.target.tagName === "LI") {
		selectButton.textContet = event.target.textContent;
		optionList.classList.add("hidden");
	}
});


