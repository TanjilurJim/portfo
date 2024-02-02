function lasttime() {
    document.getElementById('lasttime').innerHTML = new Date(document.lastModified)
}
window.onload = lasttime