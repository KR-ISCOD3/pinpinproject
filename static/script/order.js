 // Array to hold cart items
 let cart = [];
 
 // Event listener for the "Add to Cart" button
 document.querySelectorAll('.add-to-cart').forEach(button => {
     button.addEventListener('click', function () { 

        document.querySelector('.isEmpty').classList.add("d-none")

         const product = {
             id: this.dataset.id,
             name: this.dataset.name,
             price: parseFloat(this.dataset.price),
             image: this.dataset.image,
             description: this.dataset.description,
             qty: 1 // Default quantity is 1
         };

         // Add product to cart array (or update quantity if product already exists in the cart)
         let existingProduct = cart.find(item => item.id === product.id);
         if (existingProduct) {
             existingProduct.qty += 1;  // Increase quantity if product is already in the cart
         } else {
             cart.push(product); // Add new product to cart
         }

         // Update the cart table
         updateCartTable();

     });
 });
 // Event listener for quantity change
 document.addEventListener('input', function (e) {
     if (e.target.classList.contains('qty-input')) {
         const productId = e.target.dataset.id;
         const newQty = parseInt(e.target.value);
         const product = cart.find(item => item.id === productId);

         if (product) {
             product.qty = newQty;
             updateCartTable(); // Update cart after quantity change
         }
     }
 });

 // Event listener for removing items from cart
 document.addEventListener('click', function (e) {
     if (e.target.classList.contains('remove-from-cart')) {
         const productId = e.target.dataset.id;
         cart = cart.filter(item => item.id !== productId); // Remove item from cart
         if(cart.length === 0){
            document.querySelector('.isEmpty').classList.remove("d-none")
         } 
         updateCartTable(); // Update cart after removal
     }
 });

 document.querySelector('.clear-all').addEventListener('click', function(){
    // Clear the cart by setting it to an empty array
    cart = [];
    if(cart.length === 0){
        document.querySelector('.isEmpty').classList.remove("d-none")
     } 
    // Update the cart table to reflect the empty cart
    updateCartTable();
 })

// Function to update the cart table (this part remains unchanged from your existing code)
function updateCartTable() {
    const cartTable = document.querySelector('.cart-table tbody');
    cartTable.innerHTML = ''; // Clear the table

    let total = 0;

    cart.forEach(product => {
        total += product.price * product.qty;

        const row = document.createElement('tr');
        row.classList.add('align-middle');

        row.innerHTML = `
            <td style="width: 75px;height: 75px;">
                <img src="${product.image}" alt="${product.name}" class="rounded-4 object-fit-cover w-100 h-100">
            </td>
            <td>
                <p class="m-0 text-limit-1line">${product.name}</p>
                <p class="m-0 text-danger" style="font-size: 14px;">$${(product.price * product.qty).toFixed(2)}</p>
            </td>
            <td class="ps-5">
                <input type="number" class="form-control w-75 p-0 text-center shadow-none py-1 qty-input" value="${product.qty}" min="1" data-id="${product.id}">
            </td>
            <td>
                <button class="btn shadow-none bg-danger text-light remove-from-cart" data-id="${product.id}">
                    <i class="bi bi-trash remove-from-cart" data-id="${product.id}"></i>
                </button>
            </td>
        `;

        cartTable.appendChild(row);
    });

    let payment = 0;
    const rows = cartTable.querySelectorAll('tr');
    rows.forEach(row => {
        const priceElement = row.querySelector('.text-danger');
        if (priceElement) {
            const priceText = priceElement.textContent.replace('$', '');
            payment += parseFloat(priceText);
        }
    });

    document.querySelector('.total-payment').textContent = `Total: $${payment.toFixed(2)}`;
}
// Event listener for "Check Out" button (this is where we update the modal content)
document.querySelector('[data-bs-target="#CustomerModal"]').addEventListener('click', function () {
    const modalTable = document.getElementById('cartTableModal').querySelector('tbody');
    const modalTotal = document.getElementById('modalTotal');
    modalTable.innerHTML = '';  // Clear existing content in the modal

    let total = 0;

    // Loop through cart items to add them to the modal
    cart.forEach(product => {
        total += product.price * product.qty;

        const row = document.createElement('tr');
        row.classList.add('align-middle');
        row.innerHTML = `
            <td class="d-none" data-product-id="${product.id}"></td>
            <td>${product.name}</td>
            <td class="product-quantity">x${product.qty}</td>
            <td class="product-price">$${(product.price * product.qty).toFixed(2)}</td>
        `;
        modalTable.appendChild(row);
    });

    // Update the total price in the modal
    modalTotal.textContent = `Total: $${total.toFixed(2)}`;
});

document.getElementById("process-order-form").addEventListener("submit", function (e) {
    e.preventDefault(); // Prevent form submission for now

    let orderDetails = []; // Array to store all order details for each product
    let rows = document.querySelectorAll("#cartTableModal tbody tr");

    rows.forEach(row => {

        let productId = row.querySelector("td:first-child").getAttribute("data-product-id");
        let userId = document.getElementById("user_id").value;

        // Extract price (remove the '$' sign and convert to float)
        let priceText = row.querySelector(".product-price").textContent;
        let price = parseFloat(priceText.replace('$', '').trim()); 

        // Extract quantity (remove the 'x' and convert to integer)
        let quantityText = row.querySelector(".product-quantity").textContent;
        let quantity = parseInt(quantityText.replace('x', '').trim()); // Removes 'x' and trims any extra spaces

        // Calculate the total for each product (price * quantity)
        let productTotal = price * quantity;

        // Create an order object for this product
        let order = {
            product_id: productId,
            user_id: userId,          // Example: get user_id from form
            qty: quantity,
            total: productTotal,
            date: new Date().toISOString(),  // Current date and time
            // You may want to add customer_id and user_id from your session or form
        };

        // Add the order object to the orderDetails array
        orderDetails.push(order);

        // Log the order for debugging purposes
        console.log(order);
    });

    // Assign the order details to the hidden input field
    document.getElementById("order_details").value = JSON.stringify(orderDetails);

    // Now submit the form
    this.submit();
     // Reset the form and clear order details input field
     this.reset();  // Reset form fields
     document.getElementById("order_details").value = ""; // Clear order details field
});
