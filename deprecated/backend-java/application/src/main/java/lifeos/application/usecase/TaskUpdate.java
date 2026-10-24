package lifeos.application.usecase;

import java.time.LocalDate;
import lifeos.application.Change;
import lifeos.domain.Priority;

/**
 * Campos de una actualización parcial de {@link UpdateTask}.
 *
 * <p>{@code title} y {@code priority} en null significan "no tocar": no tienen
 * forma de limpiarse, consistente con que el dominio no los admite vacíos.
 * {@code description} y {@code dueDate} usan {@link Change} porque sí pueden
 * quitarse.
 */
public record TaskUpdate(
        String title, Change<String> description, Priority priority, Change<LocalDate> dueDate) {

    public static TaskUpdate none() {
        return new TaskUpdate(null, Change.unset(), null, Change.unset());
    }

    public TaskUpdate withTitle(String title) {
        return new TaskUpdate(title, description, priority, dueDate);
    }

    public TaskUpdate withDescription(String description) {
        return new TaskUpdate(title, Change.to(description), priority, dueDate);
    }

    public TaskUpdate withPriority(Priority priority) {
        return new TaskUpdate(title, description, priority, dueDate);
    }

    public TaskUpdate withDueDate(LocalDate dueDate) {
        return new TaskUpdate(title, description, priority, Change.to(dueDate));
    }
}
