const { createApp, ref } = Vue;

createApp({
    setup() {
 
        //const title_page = ref('access your account');
        const username = ref(''); 
        const password = ref('');

        const signup = async () => {
            console.log("Trying to log in with:", username.value);

            
            const url = "http://127.0.0.1:8000/token"; 
            
            const params = new URLSearchParams();
            params.append('username', username.value); 
            params.append('password', password.value);
try {
    const response = await axios.post(url, params);
    
    
    if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
        localStorage.setItem("username", username.value);

        console.log("Login OK, Redirecting...");
        
  
        window.location.href = "offboarding.html"; 
    } else {
        alert("Error: Token not received from server.");
    }

} catch (error) {
  
    console.error(error);
    alert("Login failed!");
}
        };

    
        return {
            username,
            password,
            signup
        };
    }
}).mount('#app');