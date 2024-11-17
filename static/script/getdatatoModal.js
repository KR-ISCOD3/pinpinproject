document.addEventListener("DOMContentLoaded", () => {
    const editButtons = document.querySelectorAll("#btn-edit");

    editButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        // Extract data from button
        const id = btn.getAttribute("data-id");
        const code = btn.getAttribute("data-code");
        const name = btn.getAttribute("data-name");
        const price = btn.getAttribute("data-price");
        const stock = btn.getAttribute("data-stock");
        const description = btn.getAttribute("data-description");
        const image = btn.getAttribute("data-image");

        // Populate modal fields
        document.getElementById("product_id").value = id;
        document.getElementById("upcode").value = code;
        document.getElementById("upname").value = name;
        document.getElementById("upprice").value = price;
        document.getElementById("upstock").value = stock;
        document.getElementById("updescription").value = description;

        // Update the image preview
        document.getElementById("uppic").src = image;
      });
    });
  });

  document.addEventListener("DOMContentLoaded", () => {
    const delButtons = document.querySelectorAll("#btn-del");

    delButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        // Extract data from button
        const id = btn.getAttribute("data-id");
        // Populate modal fields
        document.getElementById("del_id").value = id;
      });
    });
  });