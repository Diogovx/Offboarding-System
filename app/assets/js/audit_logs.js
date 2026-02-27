const { createApp, ref, reactive, onMounted } = Vue;

const API_BASE = 'http://127.0.0.1:8000';

axios.interceptors.request.use(cfg => {
    const token = localStorage.getItem('access_token');
    if (token) cfg.headers.Authorization = `Bearer ${token}`;
    return cfg;
});

axios.interceptors.response.use(
    r => r,
    err => {
        if (err.response?.status === 401) window.location.href = 'index.html';
        return Promise.reject(err);
    }
);

createApp({
    setup() {
        const currentUser = ref(localStorage.getItem('username') || '');
        const isAdmin = ref(false)
        const currentPage = ref('logs');
        const menuOpen = ref(false)
        const logs = ref([]);
        const loading = ref(false);
        const error = ref('');
        const exporting = ref(false);
        const exportMsg = ref('');
        const exportError = ref(false);

        const availableActions = ref([
            {label: 'Login', value: 'system_login'},
            {label: 'Offboarding (Rede)', value: 'disable_ad_user'},
            {label: 'Offboarding (InTouch)', value: 'disable_intouch_user'},
            {label: 'Offboarding (Catraca)', value: 'disable_turnstile_user'},
            {label: 'Criação de usuário', value: 'create_user'},
            {label: 'Atualização de usuário', value: 'update_user'},
            {label: 'Remoção de usuário', value: 'delete_user'},
            {label: 'Exportação de registros', value: 'export_audit_logs'},
        ]);

        const actionLabels = {
            system_login: 'Login',
            system_logout: 'Logout',
            disable_ad_user: 'Offboarding (Rede)',
            disable_intouch_user: 'Offboarding (InTouch)',
            disable_turnstile_user: 'Offboarding (Catraca)',
            export_audit_logs: 'Exportação de registros'
        };



        const filters = reactive({
            action: '',
            username: '',
            status: '',
            date_from: '',
            date_to: '',
            page: 1,
            limit: 20,
        });

        const buildParams = () => {
            const params = { page: filters.page, limit: filters.limit };
            if (filters.action) params.action = filters.action;
            if (filters.username) params.username = filters.username;
            if (filters.status) params.status = filters.status;
            if (filters.date_from) params.date_from = filters.date_from;
            if (filters.date_to) params.date_to = filters.date_to;
            return params;
        };

        const fetchLogs = async () => {
            loading.value = true;
            error.value = '';
            try {
                const { data } = await axios.get("/logs", { params: buildParams() });
                logs.value = data.items;
            } catch (e) {
                error.value = e.response?.data?.detail || 'Erro ao carregar logs.';
            } finally {
                loading.value = false;
            }
        };

        const applyFilters = () => {
            filters.page = 1;
            fetchLogs();
        };

        const clearFilters = () => {
            Object.assign(filters, { action: '', username: '', status: '', date_from: '', date_to: '', page: 1 });
            fetchLogs();
        };

        const prevPage = () => { if (filters.page > 1) { filters.page--; fetchLogs(); } };
        const nextPage = () => { filters.page++; fetchLogs(); };

        const formatDate = (iso) => {
            if (!iso) return '—';
            return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'medium' });
        };

        const exportLogs = async (format) => {
            exporting.value = true;
            exportMsg.value = 'Preparando exportação...';
            exportError.value = false;
            try {
                const payload = {
                    format,
                    filters: {
                        action: filters.action || null,
                        username: filters.username || null,
                        status: filters.status || null,
                        date_from: filters.date_from || null,
                        date_to: filters.date_to || null,
                        page: 1,
                        limit: 10000, // exportação sem paginação
                    }
                };
                const { data } = await axios.post("/logs/export", payload);
                exportMsg.value = 'Gerando arquivo, aguarde...';
                await pollDownload(data.download_url, data.job_id);
            } catch (e) {
                exportMsg.value = e.response?.data?.detail || 'Erro ao iniciar exportação.';
                exportError.value = true;
            } finally {
                exporting.value = false;
            }
        };

        const pollDownload = async (url, jobId, attempts = 0) => {
            if (attempts > 20) {
                exportMsg.value = 'Timeout na exportação. Tente novamente.';
                exportError.value = true;
                return;
            }
            try {
                const resp = await axios.get(`${url}`, { responseType: 'blob' });
                const blob = new Blob([resp.data]);
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = url.split('/').pop();
                a.click();
                exportMsg.value = 'Download iniciado com sucesso!';
                setTimeout(() => exportMsg.value = '', 4000);
            } catch (e) {
                if (e.response?.status === 404) {
                    await new Promise(r => setTimeout(r, 1500));
                    await pollDownload(url, jobId, attempts + 1);
                } else {
                    exportMsg.value = 'Erro ao baixar arquivo.';
                    exportError.value = true;
                }
            }
        };

        const logout = () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('username');
            window.location.href = 'index.html';
        };

        const checkAdmin = async () => {
            try {
                const { data } = await axios.get("/users/me");
                if (data.userRole === 1){
                    isAdmin.value = true;
                }
                else {
                    window.location.href = 'offboarding.html';
                }
            } catch {
                window.location.href = 'index.html';
            }
        };

        onMounted(async () => {
            if (!localStorage.getItem('access_token')) {
                window.location.href = 'index.html';
                return;
            }
            await checkAdmin();
            fetchLogs();
        });

        return {
            currentUser,
            menuOpen,
            isAdmin, 
            currentPage,   
            logs,
            loading,
            error,
            exporting,
            exportMsg,
            exportError,
            filters,
            availableActions,
            actionLabels,
            fetchLogs,
            applyFilters,
            clearFilters,
            prevPage,
            nextPage,
            exportLogs,
            formatDate,
            logout
        };
    }
}).mount('#app');