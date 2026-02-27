const { createApp, ref } = Vue;

createApp({
    setup() {
        const username = ref(''); 
        const password = ref('');
        const showPassword = ref(false); // Controle do olhinho
        const errorMessage = ref('');    // Feedback de erro
        const isLoading = ref(false);     // Feedback de carregamento

        const signup = async () => {
            errorMessage.value = '';
            isLoading.value = true;
            
            const url = "http://127.0.0.1:8000/token"; 
            const params = new URLSearchParams();
            params.append('username', username.value); 
            params.append('password', password.value);

            try {
                const response = await axios.post(url, params);
                
                if (response.data.access_token) {
                    localStorage.setItem("access_token", response.data.access_token);
                    localStorage.setItem("username", username.value);
                    window.location.href = "offboarding.html"; 
                } else {
                    errorMessage.value = "Token não recebido do servidor.";
                }
            } catch (error) {
                console.error(error);
                // Feedback mais amigável
                if (error.response && error.response.status === 401) {
                    errorMessage.value = "Usuário ou senha inválidos.";
                } else {
                    errorMessage.value = "Erro de conexão com o servidor.";
                }
            } finally {
                isLoading.value = false;
            }
        };

        return {
            username,
            password,
            showPassword,
            errorMessage,
            isLoading,
            signup
        };
    }
}).mount('#app');