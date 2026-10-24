package lifeos.domain;

/** Estado de una tarea dentro de su ciclo de vida. */
public enum TaskStatus {
    TODO("todo"),
    DOING("doing"),
    DONE("done");

    private final String value;

    TaskStatus(String value) {
        this.value = value;
    }

    /** Valor externo (base de datos, JSON): siempre en minúscula. */
    public String value() {
        return value;
    }

    public static TaskStatus fromValue(String value) {
        for (TaskStatus status : values()) {
            if (status.value.equals(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Estado de tarea desconocido: " + value);
    }
}
