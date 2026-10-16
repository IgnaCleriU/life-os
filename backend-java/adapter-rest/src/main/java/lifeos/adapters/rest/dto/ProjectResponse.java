package lifeos.adapters.rest.dto;

import lifeos.domain.Project;

/** Representación de un Project en las respuestas REST ({@code deleted_at} no se expone). */
public record ProjectResponse(String id, String name, String description, String status, String createdAt) {

    public static ProjectResponse from(Project project) {
        return new ProjectResponse(
                project.id().toString(),
                project.name(),
                project.description(),
                project.status().value(),
                JsonTimestamps.format(project.createdAt()));
    }
}
