package lifeos.adapters.rest.dto;

/** Body de {@code POST /tasks/{id}/move}. */
public record TaskMoveRequest(String projectId) {}
