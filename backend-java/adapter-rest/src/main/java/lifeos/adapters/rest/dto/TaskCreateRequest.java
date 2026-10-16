package lifeos.adapters.rest.dto;

/**
 * Body de {@code POST /projects/{id}/tasks}. Los campos llegan como texto y se
 * convierten en el controller, para que un valor inválido sea un 422 propio.
 */
public record TaskCreateRequest(String title, String description, String priority, String dueDate) {}
