document.getElementById("image").onchange = (e) => {
    var file = e.target.files[0];
    document.getElementById("pic").src = URL.createObjectURL(file)
}

document.getElementById("upimage").onchange = (e) => {
    var file = e.target.files[0];
    document.getElementById("uppic").src = URL.createObjectURL(file)
}