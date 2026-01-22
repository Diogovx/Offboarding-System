const { createApp, ref } = Vue

createApp({
    setup() {
 
        const title_page = ref('Connect your account')
        const email = ref('')
        const password = ref('')

        function signup() {
            console.log('Login in progress:', email.value, password.value)
            alert('Login submitted! Check the console.')
        }

        return {
            title_page,
            email,
            password,
            signup
        }
    }
}).mount('#app')