document.getElementById("show").onclick = () =>{
    document.getElementById("show").classList.add("d-none")
    document.getElementById("hide").classList.remove("d-none")
    document.getElementById("pass").setAttribute("type","text")
}

document.getElementById("hide").onclick = () =>{
    document.getElementById("hide").classList.add("d-none")
    document.getElementById("show").classList.remove("d-none")
    document.getElementById("pass").setAttribute("type","password")
}
