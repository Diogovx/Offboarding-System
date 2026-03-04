const { createApp, ref, onMounted, computed } = Vue;

createApp({
  setup() {
    const users = ref([]);
    const userLogs = ref([]);
    const currentUser = ref(localStorage.getItem("username") || "Admin");
    const isAdmin = ref(false);
    const currentPage = ref("users_management");

    const searchQuery = ref("");
    const statusFilter = ref("all");
    const menuOpen = ref(false);

    const feedback = ref("");
    const formError = ref("");
    const loadingHistory = ref(false);
    const modals = ref({ form: false, history: false });
    const isEditing = ref(false);

    const selectedUser = ref({});
    const originalForm = ref(null);
    const confirmPassword = ref("");
    const form = ref({
      username: "",
      email: "",
      password: "",
      userRole: 3,
      enabled: true,
    });

    onMounted(() => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        window.location.href = "index.html";
        return;
      }

      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      axios.defaults.baseURL = "";

      axios.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response && error.response.status === 401) {
            localStorage.clear();
            window.location.href = "index.html";
          }
          return Promise.reject(error);
        }
      );

      checkAdmin();
      getUsers();
    });

    const filteredUsers = computed(() => {
      return users.value.filter((u) => {
        const matchesSearch = u.username
          .toLowerCase()
          .includes(searchQuery.value.toLowerCase());
        const matchesStatus =
          statusFilter.value === "all"
            ? true
            : statusFilter.value === "active"
            ? u.enabled
            : !u.enabled;
        return matchesSearch && matchesStatus;
      });
    });

    const isDirty = computed(() => {
      if (!isEditing.value || !originalForm.value) return true;
      const f = form.value;
      const o = originalForm.value;
      return (
        f.username !== o.username ||
        f.email    !== o.email    ||
        f.userRole !== o.userRole ||
        f.enabled  !== o.enabled  ||
        (f.password && f.password.length > 0)
      );
    });

    const passwordCriteria = computed(() => {
      const p = form.value.password;
      return {
        length:  p.length >= 8,
        upper:   /[A-Z]/.test(p),
        lower:   /[a-z]/.test(p),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(p),
      };
    });

    const passwordsMatch = computed(() => form.value.password === confirmPassword.value);

    const isFormValid = computed(() => {
      if (isEditing.value && !isDirty.value) return false;

      const usernameRegex = /^[a-z0-9]+\.[a-z0-9]+$/i;
      const hasValidUsername = form.value.username && usernameRegex.test(form.value.username);
      const hasEmail    = form.value.email    && /^\S+@\S+\.\S+$/.test(form.value.email);
      if (!hasValidUsername || !hasEmail) return false;

      if (isEditing.value) {
        if (!form.value.password) return true;
        const c = passwordCriteria.value;
        return c.length && c.upper && c.lower && c.special && passwordsMatch.value;
      } else {
        const c = passwordCriteria.value;
        return c.length && c.upper && c.lower && c.special && passwordsMatch.value;
      }
    });

    const checkAdmin = async () => {
      try {
        const { data } = await axios.get("/users/me");
        isAdmin.value = data.userRole === 1;
        if (!isAdmin.value) {
          alert("Acesso negado: apenas administradores.");
          window.location.href = "offboarding.html";
        }
      } catch {
        isAdmin.value = false;
      }
    };

    const getUsers = async () => {
      try {
        const res = await axios.get("/users/");
        users.value = res.data.users;
      } catch (err) {
        console.error("Erro ao carregar usuários:", err);
      }
    };

    const parseUtcDate = (raw) => {
      if (!raw) return null;
      const s = String(raw).trim();
      const hasOffset = /[Z]$/i.test(s) || /[+-]\d{2}:\d{2}$/.test(s);
      const normalized = hasOffset ? s : s + "Z";
      const d = new Date(normalized);
      return isNaN(d.getTime()) ? null : d;
    };

    const formatLogDate = (log) => {
      const raw = log.created_at ?? log.timestamp ?? log.date ?? log.createdAt ?? null;
      const d = parseUtcDate(raw);
      if (!d) return raw ? String(raw) : "—";
      return d.toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
    };

    const viewHistory = async (user) => {
      selectedUser.value = user;
      modals.value.history = true;
      loadingHistory.value = true;
      userLogs.value = [];
      try {
        const res = await axios.get(`/logs?username=${user.username}&limit=10`);
        const raw = res.data;
        userLogs.value = Array.isArray(raw)
          ? raw
          : (raw.logs ?? raw.items ?? raw.results ?? []);
      } catch (e) {
        console.error("Erro ao carregar histórico:", e);
        userLogs.value = [];
      } finally {
        loadingHistory.value = false;
      }
    };

    const openModal = (mode, user = null) => {
      feedback.value  = "";
      formError.value = "";
      confirmPassword.value = "";
      isEditing.value = mode === "edit";

      if (isEditing.value && user) {
        selectedUser.value = user;
        const snapshot = {
          username: user.username,
          email:    user.email,
          password: "",
          userRole: user.userRole,
          enabled:  user.enabled,
        };
        form.value         = { ...snapshot };
        originalForm.value = { ...snapshot };
      } else {
        originalForm.value = null;
        form.value = { username: "", email: "", password: "", userRole: 3, enabled: true };
      }
      modals.value.form = true;
    };

    const submitForm = async () => {
      if (!isFormValid.value) return;
      formError.value = "";

      try {
        if (isEditing.value) {
          const payload = {};
          const f = form.value;
          const o = originalForm.value;

          if (f.username !== o.username) payload.username = f.username;
          if (f.email    !== o.email)    payload.email    = f.email;
          if (f.userRole !== o.userRole) payload.userRole = f.userRole;
          if (f.enabled  !== o.enabled)  payload.enabled  = f.enabled;
          if (f.password)                payload.password = f.password;

          await axios.put(`/users/${selectedUser.value.id}`, payload);
          feedback.value = "Usuário atualizado com sucesso!";
        } else {
          await axios.post("/users/", {
            username: form.value.username,
            email:    form.value.email,
            password: form.value.password,
            userRole: form.value.userRole,
            enabled:  form.value.enabled,
          });
          feedback.value = "Usuário criado com sucesso!";
        }

        setTimeout(() => {
          modals.value.form = false;
          getUsers();
        }, 1500);
      } catch (e) {
        const detail = e.response?.data?.detail;
        if (Array.isArray(detail)) {
          formError.value = detail.map(d => d.msg || JSON.stringify(d)).join(" | ");
        } else {
          formError.value = detail || "Erro inesperado. Tente novamente.";
        }
      }
    };

    const logout = () => {
      localStorage.clear();
      window.location.href = "index.html";
    };

    return {
      users, userLogs, currentUser, isAdmin,
      searchQuery, statusFilter, currentPage, menuOpen,
      confirmPassword, passwordCriteria, passwordsMatch,
      isFormValid, isDirty, feedback, formError,
      loadingHistory, modals, isEditing, selectedUser,
      form, filteredUsers,
      formatLogDate, viewHistory, openModal, submitForm, logout,
    };
  },
}).mount("#app");