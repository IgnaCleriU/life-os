package lifeos.domain;

import java.time.Instant;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

/**
 * Una tarea perteneciente a un proyecto.
 *
 * <p>Las transiciones de estado y las invariantes viven acá.
 */
public final class Task {

    private final UUID id;
    private UUID projectId;
    private String title;
    private String description;
    private TaskStatus status;
    private Priority priority;
    private LocalDate dueDate;
    private final Instant createdAt;
    private Instant deletedAt;

    /** Rehidrata una tarea existente (lo usan los repositorios). */
    public Task(
            UUID id,
            UUID projectId,
            String title,
            String description,
            TaskStatus status,
            Priority priority,
            LocalDate dueDate,
            Instant createdAt,
            Instant deletedAt) {
        this.id = Objects.requireNonNull(id);
        this.projectId = Objects.requireNonNull(projectId);
        this.title = Objects.requireNonNull(title);
        this.description = description;
        this.status = Objects.requireNonNull(status);
        this.priority = Objects.requireNonNull(priority);
        this.dueDate = dueDate;
        this.createdAt = Objects.requireNonNull(createdAt);
        this.deletedAt = deletedAt;
    }

    /** Crea una tarea nueva con prioridad media, sin fecha ni descripción. */
    public static Task create(UUID projectId, String title) {
        return create(projectId, title, Priority.MEDIUM, null, null);
    }

    /** Crea una tarea nueva, generando id y timestamp en el dominio. */
    public static Task create(
            UUID projectId, String title, Priority priority, LocalDate dueDate, String description) {
        return new Task(
                UUID.randomUUID(),
                projectId,
                validateTitle(title),
                description,
                TaskStatus.TODO,
                priority,
                dueDate,
                Timestamps.now(),
                null);
    }

    private static String validateTitle(String title) {
        String cleaned = title == null ? "" : title.strip();
        if (cleaned.isEmpty()) {
            throw new DomainValidationException("El título de la tarea no puede estar vacío");
        }
        return cleaned;
    }

    public UUID id() {
        return id;
    }

    public UUID projectId() {
        return projectId;
    }

    public String title() {
        return title;
    }

    public String description() {
        return description;
    }

    public TaskStatus status() {
        return status;
    }

    public Priority priority() {
        return priority;
    }

    public LocalDate dueDate() {
        return dueDate;
    }

    public Instant createdAt() {
        return createdAt;
    }

    public Instant deletedAt() {
        return deletedAt;
    }

    /** Si la tarea está borrada lógicamente. */
    public boolean isDeleted() {
        return deletedAt != null;
    }

    /** Cambia el título de la tarea, validando la invariante. */
    public void rename(String newTitle) {
        this.title = validateTitle(newTitle);
    }

    /** Cambia la descripción (o la quita si es null). */
    public void describe(String description) {
        this.description = description;
    }

    /** Mueve la tarea a otro proyecto. */
    public void moveTo(UUID projectId) {
        this.projectId = Objects.requireNonNull(projectId);
    }

    /** Cambia la prioridad de la tarea. */
    public void changePriority(Priority priority) {
        this.priority = Objects.requireNonNull(priority);
    }

    /** Reprograma la fecha límite (o la quita si es null). */
    public void reschedule(LocalDate dueDate) {
        this.dueDate = dueDate;
    }

    /** Marca la tarea como en curso. */
    public void start() {
        this.status = TaskStatus.DOING;
    }

    /** Marca la tarea como completada (idempotente). */
    public void complete() {
        this.status = TaskStatus.DONE;
    }

    /** Vuelve la tarea a pendiente. */
    public void reopen() {
        this.status = TaskStatus.TODO;
    }

    /**
     * Borra la tarea lógicamente (idempotente).
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
