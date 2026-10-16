package lifeos.adapters.rest.dto;

/** Body de {@code POST /projects}. */
public record ProjectCreateRequest(String name, String description) {}
