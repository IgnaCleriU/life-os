package lifeos.domain;

/**
 * Estado de un proyecto.
 *
 * <p>Los tres estados son mutuamente excluyentes y las transiciones entre ellos
 * son libres (cualquiera → cualquiera): un proyecto puede completarse y volver a
 * activarse, o archivarse desde cualquier estado y desarchivarse.
 */
public enum ProjectStatus {
    ACTIVE("active"),
    COMPLETED("completed"),
    ARCHIVED("archived");

    private final String value;

    ProjectStatus(String value) {
        this.value = value;
    }

    /** Valor externo (base de datos, JSON): siempre en minúscula. */
    public String value() {
        return value;
    }

    public static ProjectStatus fromValue(String value) {
        for (ProjectStatus status : values()) {
            if (status.value.equals(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Estado de proyecto desconocido: " + value);
    }
}
