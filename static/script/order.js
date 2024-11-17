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

// Function to update the cart table
function updateCartTable() {
    const cartTable = document.querySelector('.cart-table tbody');
    cartTable.innerHTML = ''; // Clear the table

    let total = 0;

    cart.forEach(product => {
        total += product.price * product.qty;

        // Create a new row in the cart table
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

}

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

// Handle the "Calculate" button click event
document.querySelector('.btn-calculate').addEventListener('click', function () {
    const cartTableRows = document.querySelectorAll('.cart-table tbody tr');
    
    let total = 0;

    cartTableRows.forEach(row => {
        const priceElement = row.querySelector('.text-danger'); // Get the <p> with class 'text-danger' (price)
        if (priceElement) {
            const priceText = priceElement.textContent.replace('$', ''); // Remove '$' symbol
            total += parseFloat(priceText); // Add the price to the total
        }
    });

    // Update the total in the total price section
    document.querySelector('.total-payment').textContent = `Total: $${total.toFixed(2)}`;
});
