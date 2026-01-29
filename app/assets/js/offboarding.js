const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
   
        const currentUser = ref(localStorage.getItem('username') || 'Usuário');
        const searchQuery = ref('');      
        const foundUser = ref(null);       
        
        const isLoading = ref(false);      
        const isProcessing = ref(false);   

        
        const searchMessage = ref('');
        const searchStatusClass = ref('');
        const actionMessage = ref('');
        const actionClass = ref('');
        const listServices = ref([]);

        onMounted(() => {
            const token = localStorage.getItem('access_token');
            
   
            if (!token) {
                window.location.href = 'index.html';
                return;
            }

            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            axios.defaults.baseURL = 'http://127.0.0.1:8000'; 
        });

        
        const searchUser = async () => {
           
            if (!searchQuery.value.trim()) return;

            isLoading.value = true;
            searchMessage.value = '';
            foundUser.value = null; 
            actionMessage.value = ''; 
            listServices.value = []; 

            try {   
       
                const response = await axios.get(`/intouch/${searchQuery.value}`);
               
                foundUser.value = response.data;
                listServices.value = response.data.services || []
               
                
            } catch (error) {
                console.error("error in search:", error);
                
                if (error.response && error.response.status === 404) {
                    searchMessage.value = "User not found (check registration)";
                    searchStatusClass.value = "text-yellow-600 font-medium";
                } else {
                    searchMessage.value = "Error connecting to the server.";
                    searchStatusClass.value = "text-red-500 font-medium";
                }
            } finally {
                isLoading.value = false;
            }
        };

       
        const executeOffboarding = async () => {
    if (!foundUser.value) return;

   
    const registration = foundUser.value.registration;

    const confirmation = window.confirm(`Do you wish to deactivate the collaborator? ${foundUser.value.name || registration}?`);
    if (!confirmation) return;

    isProcessing.value = true;
    actionMessage.value = '';

    try {
       
        const response = await axios.post(`/offboarding/execute/${registration}`);

        if (response.data.success) {

            actionMessage.value = `Success! Systems affected: ${response.data.details.join(", ")}`;
            actionClass.value = "bg-green-50 border-green-500 text-green-700";
        }
    } catch (error) {
        console.error("Offboarding error", error);
        const msg = error.response?.data?.detail || "Internal error processing shutdown.";
        actionMessage.value = `failure: ${msg}`;
        actionClass.value = "bg-red-50 border-red-500 text-red-700";
    } finally {
        isProcessing.value = false;
    }
};


        const logout = () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('username');
            window.location.href = 'index.html';
        };


        return { 
            currentUser, 
            searchQuery, 
            foundUser, 
            isLoading, 
            isProcessing,
            searchMessage,
            searchStatusClass,
            actionMessage,
            actionClass,
            listServices,
            searchUser, 
            executeOffboarding, 
            logout 
        };
    }
}).mount('#app');