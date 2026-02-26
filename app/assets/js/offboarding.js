const { createApp, ref, onMounted, computed } = Vue;

createApp({
  setup() {
    const currentUser = ref(localStorage.getItem("username") || "");
    const isAdmin = ref(false);
    const menuOpen = ref(false);
    const currentPage = ref('offboarding');

    const searchQuery = ref("");
    const foundUser = ref(null);

    const isLoading = ref(false);
    const isProcessing = ref(false);
    const showConfirmModal = ref(false);

    const lastOffboarding = ref(null);

    const searchMessage = ref("");
    const searchStatusClass = ref("");
    const actionMessage = ref("");
    const actionClass = ref("");
    const listServices = ref([]);
    
    onMounted(() => {
        const token = localStorage.getItem("access_token");
        
        if (!token) {
            window.location.href = "index.html";
            return;
        }
        
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        axios.defaults.baseURL = "";
        
        axios.interceptors.response.use(
            response => response,
            error => {
                if (error.response && error.response.status === 401) {
                    localStorage.removeItem("access_token");
                    window.location.href = "index.html";
                }
            return Promise.reject(error);
            }
        );

        checkAdmin()
    });
    const checkAdmin = async () => {
        try {
            const { data } = await axios.get("/users/me");
            isAdmin.value = data.userRole === 1;
        } catch {
            isAdmin.value = false;
        }
    };

    const isOffboarded = computed(() => {
        if (foundUser.value && foundUser.value.is_active === true) {
            return false;
        }
        if (lastOffboarding.value) {
            return true;
        }
        if (foundUser.value && foundUser.value.is_active === false) {
            return true;
        }

        return false;
    });
    const displayServices = computed(() => {
        if (listServices.value && listServices.value.length > 0) {
            return listServices.value;
        }
        if (lastOffboarding.value && lastOffboarding.value.revoked_systems) {
            return lastOffboarding.value.revoked_systems.map(s => ({ name: s, active: false }));
        }
        return [];
    });
    const servicesToDeactivateString = computed(() => {
        if (!listServices.value || listServices.value.length === 0) return "";
        
        return listServices.value
            .filter(s => s.active)
            .map(s => s.name)
            .join(', ');
    });

    const searchUser = async () => {
        if (!searchQuery.value.trim()) return;

        isLoading.value = true;
        searchMessage.value = "";

        actionMessage.value = "";

        foundUser.value = null;
        listServices.value = [];
        lastOffboarding.value = null;

        try {
            const response = await axios.get(`/intouch/${searchQuery.value}`);
            const response_services = await axios.get(`/offboarding/search/${searchQuery.value}`);
            const response_history = await axios.get(`/offboarding/history/`, {
                params: { registration: searchQuery.value, limit: 1 }
            });

            if (response.data && response.data.found === true) {
                foundUser.value = response.data;
                const servicesObj = response_services.data || {};
                listServices.value = Object.keys(servicesObj).map(key => ({
                    name: key,
                    active: servicesObj[key]
                }));

                if(response_history.data && response_history.data.total > 0){
                    lastOffboarding.value = response_history.data.items[0];
                }
            } else {
                searchMessage.value = "Matrícula não encontrada no sistema.";
                searchStatusClass.value = "text-red-500 font-medium";
            }
        } catch (error) {
                console.error("Search error:", error);
                searchMessage.value = "Erro de conexão.";
                searchStatusClass.value = "text-red-500 font-medium";
        } finally {
            isLoading.value = false;
        }
    };

    const executeOffboarding = () => {
        showConfirmModal.value = true;
    };

    const confirmOffboarding = async () => {
        if (!foundUser.value) return;

        isProcessing.value = true;

        try {
            const registration = foundUser.value.registration;
            const response = await axios.post(
                `/offboarding/execute/${registration}`,
            );
        if (response.data.success) {
            showConfirmModal.value = false;
            actionMessage.value = `Sucesso! Sistemas afetados: ${response.data.details.join(", ")}.`;
            actionClass.value = "bg-green-50 border-green-500 text-green-700";
            foundUser.value = null;
            lastOffboarding.value = null;
        }
        } catch (error) {
            const msg = error.response?.data?.detail || "Erro ao processar.";
            actionMessage.value = `Falha: ${msg}`;
            actionClass.value = "bg-red-50 border-red-500 text-red-700";
            showConfirmModal.value = false;
        } finally {
            isProcessing.value = false;
        }
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("username");
        window.location.href = "index.html";
    };

    return {
        currentUser,
        isAdmin,
        currentPage,
        searchQuery,
        foundUser,
        menuOpen,
        isLoading,
        isProcessing,
        searchMessage,
        searchStatusClass,
        actionMessage,
        actionClass,
        listServices,
        showConfirmModal,
        lastOffboarding,
        isOffboarded,
        displayServices,
        servicesToDeactivateString,
        searchUser,
        executeOffboarding,
        confirmOffboarding,
        logout,
    };
  },
}).mount("#app");
