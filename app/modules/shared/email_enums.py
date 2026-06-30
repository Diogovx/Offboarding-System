EMAIL_TEMPLATES = {
    "pt": {
        "subject": "Log de Desligamento - {registration}",
        "success_title": "\nSistemas afetados com sucesso:",
        "no_systems": "\nAtenção: Nenhum sistema afetado com sucesso.",
        "body": (
            "O usuário {user_target} com o registro {registration} "
            "passou pelo processo de: ({action_value}).\n"
            "Executor: {performed_by}\n"
            "{txt_details}\n"
            "Data/Hora: {now}"
        ),
        "zoneinfo": "America/Sao_Paulo"
    },
    "en": {
        "subject": "Offboarding Log - {registration}",
        "success_title": "\nSuccessfully affected systems:",
        "no_systems": "\nWarning: No systems were successfully affected.",
        "body": (
            "The user {user_target} with registration {registration} "
            "went through the process of: ({action_value}).\n"
            "Performed by: {performed_by}\n"
            "{txt_details}\n"
            "Date/Time: {now}"
        ),
        "zoneinfo": "America/Los_Angeles"
    },
    "id": {
        "subject": "Log Offboarding - {registration}",
        "success_title": "\nSistem yang berhasil dipengaruhi:",
        "no_systems": "\nPeringatan: Tidak ada sistem yang berhasil dipengaruhi.",
        "body": (
            "Pengguna {user_target} dengan nomor induk {registration} "
            "telah melalui proses: ({action_value}).\n"
            "Pelaksana: {performed_by}\n"
            "{txt_details}\n"
            "Tanggal/Waktu: {now}"
        ),
        "zoneinfo": "Asia/Jakarta"
    },
    "ar": {
        "subject": "سجل خروج الموظف - {registration}",
        "success_title": "\nالأنظمة التي تم تأثرها بنجاح:",
        "no_systems": "\nتنبيه: لم يتم التأثير على أي نظام بنجاح.",
        "body": (
            "المستخدم {user_target} صاحب الرقم الوظيفي {registration} "
            "مر بعملية: ({action_value}).\n"
            "المنفذ: {performed_by}\n"
            "{txt_details}\n"
            "التاريخ/الوقت: {now}"
        ),
        "zoneinfo": "Asia/Riyadh"
    }
}
