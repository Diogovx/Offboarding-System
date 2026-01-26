const { createApp, ref } = Vue;

createApp({
    setup() {
        const title_page = ref('Connect your account');
        const username = ref(''); 
        const password = ref('');

       
        async function signup() {
            console.log("Trying to log in with:", username.value);
            

            const url = "http://127.0.0.1:8000/token";
            
            const params = new URLSearchParams();
            params.append('username', username.value); 
            params.append('password', password.value);

            try {
                const response = await axios.post(url, params);
                localStorage.setItem("access_token", response.data.access_token);
                alert("Success!");
                window.location.href = "/dashboard"; 
            } catch (error) {
                const msg = error.response?.data?.detail || "Connection error";
                alert("Login failed: " + msg);
            }
        }

       
        return {
            title_page,
            username,
            password,
            signup
        };
    }
}).mount('#app');