// Gestionare coș virtual
window.onload = function () {
    const nr_of_products = document.getElementById('nr_of_products');
    const sort_by = document.getElementById('sorting');
    var virtualCart = JSON.parse(localStorage.getItem('virtualCart')) || []; // Default array gol dacă nu există coș
    var final_price=document.getElementById('final_price');

    // Inițializează aplicația
    function init() {
        if (virtualCart.length) {
            displayProducts();
            updateTotalPrice();
            updateProductCount();
            sortProducts();
            sendOrder();
            sort_by.style.display='block';
        } else {
            nr_of_products.innerHTML = 'The cart is empty';
            sort_by.style.display='none';
        }


        sort_by.addEventListener('change',sortProducts);
    }

    // Actualizează prețul total
    function updateTotalPrice() {
        let total = 0;
        for (let i = 0; i < virtualCart.length; i++) {
            total += virtualCart[i].quantity * virtualCart[i].price;
        }
        final_price.textContent = `Total: ${total.toFixed(2)} lei`;
    }

    // Actualizează numărul total de produse din coș
    function updateProductCount() {
        let total=0;
            for (let i=0;i<virtualCart.length;i++){
                total += virtualCart[i].quantity;
            }
            nr_of_products.innerHTML = `${total} products in cart`;
    }

    // Creează și afișează produsele din coș
    function displayProducts() {
        virtualCart.forEach((product, index) => {
            createProductElement(product, index);
        });
    }

    // Creează un element HTML pentru un produs
    function createProductElement(product, index) {
        const product_detail = document.createElement('div');
        product_detail.id = `product-${product.id}-${product.size}`;
        product_detail.style.border = '1px solid black';
        document.body.appendChild(product_detail);

        // Creează element pentru numele produsului
        const productName = document.createElement('p');
        productName.textContent = `${product.name} - ${product.size}`;
        product_detail.appendChild(productName);

        // Creează element pentru prețul produsului
        const price = document.createElement('p');
        price.id = `price-${index}`;
        price.textContent = `${(product.quantity * product.price).toFixed(2)} lei`;
        product_detail.appendChild(price);

        // Creează butonul de eliminare produs
        const btn_remove = document.createElement('button');
        btn_remove.textContent = 'Remove';
        btn_remove.onclick = () => removeProduct(product);
        product_detail.appendChild(btn_remove);

        // Creează input pentru cantitatea produsului
        const currentQuantity = document.createElement('input');
        currentQuantity.type = 'number';
        currentQuantity.id = `currentQuantity-${index}`;
        currentQuantity.min = '1';
        currentQuantity.value = product.quantity;
        product_detail.appendChild(currentQuantity);

        // Creează butonul pentru a scădea cantitatea
        const btn_minus = document.createElement('button');
        btn_minus.textContent = '-';
        btn_minus.onclick = () => updateQuantity(product, index, -1);
        product_detail.appendChild(btn_minus);

        // Creează butonul pentru a crește cantitatea
        const btn_plus = document.createElement('button');
        btn_plus.textContent = '+';
        btn_plus.onclick = () => updateQuantity(product, index, 1);
        product_detail.appendChild(btn_plus);

    }


    // Șterge un produs din coș
    function removeProduct(product) {
        const productIndex = virtualCart.findIndex(x => x.id === product.id && x.size === product.size);
        if (productIndex !== -1) {
            virtualCart.splice(productIndex, 1);
            localStorage.setItem('virtualCart', JSON.stringify(virtualCart));
            document.getElementById(`product-${product.id}-${product.size}`).remove();

            if (virtualCart.length === 0) {
                nr_of_products.innerHTML = 'The cart is empty';
                final_price.textContent = '';
                sort_by.style.display='none';
                const footer = document.querySelector('footer'); 
                if (footer) {
                    footer.style.display = 'none';
                }
            } else {
                updateTotalPrice();
                updateProductCount();
            }
        }
    }

    // Actualizează cantitatea unui produs
    function updateQuantity(product, index, delta) {
        const currentQuantity = document.getElementById(`currentQuantity-${index}`);
        const newQuantity = parseInt(currentQuantity.value) + delta;
        if (newQuantity >= 1) {
            product.quantity = newQuantity;
            currentQuantity.value = newQuantity;
            document.getElementById(`price-${index}`).textContent = `${(product.quantity * product.price).toFixed(2)} lei`;
            localStorage.setItem('virtualCart', JSON.stringify(virtualCart));
            updateTotalPrice();
            updateProductCount();
        }
    }

    //functie pentru sortarea produselor
    function sortProducts(){
        const sort_by = document.getElementById('sorting');
        var selected_sort=sort_by.value;

        console.log("Sorting by:", selected_sort)
        
        //sortare dupa nume sau pret
        if(selected_sort === "sort_by_name"){
            virtualCart.sort((a,b)=>a.name.localeCompare(b.name));
        }else if (selected_sort === "sort_by_price"){
            virtualCart.sort((a,b)=>(a.price*a.quantity)-(b.price*b.quantity));
        }

        clearProducts(); //sterg produsele afisate anterior
        displayProducts(); //fac o noua afisare
    }

    //functie ce sterge toate produsele de pe pagina
    function clearProducts(){
        const productList=document.querySelectorAll('div[id^="product-"]');
        productList.forEach(product => product.remove());
    }

    function getCSRFToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        return csrfToken;
    }
    
    function sendOrder() {
        const placeOrderButton = document.getElementById('place_order');
        placeOrderButton.style.display = 'block';
    
        placeOrderButton.onclick = function () {
            if (virtualCart.length === 0) {
                alert('The cart is empty');
                return;
            }
    
            fetch('http://127.0.0.1:8000/app/order_sent/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ cart: virtualCart })
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.json().then(data => {
                        console.log(data.error || 'The order could not be placed.');
                    });
                }
            })
            .then(data => {
                if (data.order_id) {
                    localStorage.removeItem('virtualCart');
                    console.log('Order placed successfully!');
                    virtualCart = []; // Golește coșul virtual
                    window.location.href = `http://127.0.0.1:8000/app/confirmation_order_sent/${data.order_id}/`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An unexpected error occurred.');
            });
        };
    }
    
    

    // Inițializare
    init();
};
