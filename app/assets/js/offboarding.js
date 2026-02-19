const { createApp, ref, onMounted } = Vue;

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

    const searchUser = async () => {
        if (!searchQuery.value.trim()) return;

        isLoading.value = true;
        searchMessage.value = "";

        foundUser.value = null;
        listServices.value = [];

        try {
            const response = await axios.get(`/intouch/${searchQuery.value}`);

            if (response.data && response.data.found === true) {
                foundUser.value = response.data;
                listServices.value = response.data.services || [];
            } else {
                searchMessage.value = "Registration number not found in the system.";
                searchStatusClass.value = "text-red-500 font-medium";
            }
        } catch (error) {
                console.error("Search error:", error);
                searchMessage.value = "Connection error.";
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
            actionMessage.value = `Success! Systems affected: ${response.data.details.join(", ")}`;
            actionClass.value = "bg-green-50 border-green-500 text-green-700";
            foundUser.value = null;
        }
        } catch (error) {
        const msg =
            error.response?.data?.detail || "Error processing offboarding.";
        actionMessage.value = `Failed: ${msg}`;
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
        searchUser,
        executeOffboarding,
        confirmOffboarding,
        logout,
    };
  },
}).mount("#app");
