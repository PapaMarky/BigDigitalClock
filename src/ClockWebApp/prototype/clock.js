function selectTab(tabName) {
    document.getElementById(tabName).style.display = "block";
    document.getElementById(tabName + "Tab").className += " w3-red";
}
function openTab(evt, tabName) {
    var i, x, tablinks;
    x = document.getElementsByClassName("clocktab");
    for (i = 0; i < x.length; i++) {
	x[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < x.length; i++) {
	tablinks[i].className = tablinks[i].className.replace(" w3-red", "");
    }
    selectTab(tabName);
}
