package lifeos.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

/**
 * Un proyecto que agrupa tareas.
 *
 * <p>Las reglas de negocio (invariantes y transiciones) viven acá; ninguna capa
 * externa debería duplicarlas.
 */
public final class Project {

    private final UUID id;
    private String name;
    private String description;
    private ProjectStatus status;
    private final Instant createdAt;
    private Instant deletedAt;

    /** Rehidrata un proyecto existente (lo usan los repositorios). */
    public Project(
            UUID id,
            String name,
            String description,
            ProjectStatus status,
            Instant createdAt,
            Instant deletedAt) {
        this.id = Objects.requireNonNull(id);
        this.name = Objects.requireNonNull(name);
        this.description = description;
        this.status = Objects.requireNonNull(status);
        this.createdAt = Objects.requireNonNull(createdAt);
        this.deletedAt = deletedAt;
    }

    /** Crea un proyecto nuevo, generando id y timestamp en el dominio. */
    public static Project create(String name, String description) {
        return new Project(
                UUID.randomUUID(),
                validateName(name),
                description,
                ProjectStatus.ACTIVE,
                Timestamps.now(),
                null);
    }

    private static String validateName(String name) {
        String cleaned = name == null ? "" : name.strip();
        if (cleaned.isEmpty()) {
            throw new DomainValidationException("El nombre del proyecto no puede estar vacío");
        }
        return cleaned;
    }

    public UUID id() {
        return id;
    }

    public String name() {
        return name;
    }

    public String description() {
        return description;
    }

    public ProjectStatus status() {
        return status;
    }

    public Instant createdAt() {
        return createdAt;
    }

    public Instant deletedAt() {
        return deletedAt;
    }

    /** Si el proyecto está borrado lógicamente. */
    public boolean isDeleted() {
        return deletedAt != null;
    }

    /** Cambia el nombre del proyecto, validando la invariante. */
    public void rename(String newName) {
        this.name = validateName(newName);
    }

    /** Cambia la descripción (o la quita si es null). */
    public void describe(String description) {
        this.description = description;
    }

    /** Marca el proyecto como finalizado. */
    public void complete() {
        this.status = ProjectStatus.COMPLETED;
    }

    /** Marca el proyecto como archivado. */
    public void archive() {
        this.status = ProjectStatus.ARCHIVED;
    }

    /** Vuelve a poner el proyecto como activo (desde completado o archivado). */
    public void activate() {
        this.status = ProjectStatus.ACTIVE;
    }

    /**
     * Borra el proyecto lógicamente (idempotente).
     *
     * <p>No se pisa un {@code deletedAt} ya puesto: reborrar no debe mover la
     * marca de tiempo del borrado original.
     */
    public void delete() {
        if (deletedAt == null) {
            deletedAt = Timestamps.now();
        }
    }

    /** Deshace el borrado lógico (idempotente). */
    public void restore() {
        this.deletedAt = null;
    }
}
