package lifeos.adapters.rest.dto;

import lifeos.domain.Task;

/** Representación de una Task en las respuestas REST ({@code deleted_at} no se expone). */
public record TaskResponse(
        String id,
        String projectId,
        String title,
        String description,
        String status,
        String priority,
        String dueDate,
        String createdAt) {

    public static TaskResponse from(Task task) {
        return new TaskResponse(
                task.id().toString(),
                task.projectId().toString(),
                task.title(),
                task.description(),
                task.status().value(),
                task.priority().value(),
                task.dueDate() == null ? null : task.dueDate().toString(),
                JsonTimestamps.format(task.createdAt()));
    }
}
