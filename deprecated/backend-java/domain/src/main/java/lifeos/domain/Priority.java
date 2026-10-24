package lifeos.domain;

/** Prioridad de una tarea. */
public enum Priority {
    LOW("low"),
    MEDIUM("medium"),
    HIGH("high");

    private final String value;

    Priority(String value) {
        this.value = value;
    }

    /** Valor externo (base de datos, JSON): siempre en minúscula. */
    public String value() {
        return value;
    }

    public static Priority fromValue(String value) {
        for (Priority priority : values()) {
            if (priority.value.equals(value)) {
                return priority;
            }
        }
        throw new IllegalArgumentException("Prioridad desconocida: " + value);
    }
}
