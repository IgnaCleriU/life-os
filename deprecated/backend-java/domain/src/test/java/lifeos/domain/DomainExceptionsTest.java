package lifeos.domain;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.UUID;
import org.junit.jupiter.api.Test;

/** Los mensajes llegan tal cual al cliente REST: tienen que coincidir con los de Python. */
class DomainExceptionsTest {

    private static final UUID ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    @Test
    void notFoundAndNotEmptyCarryIdAndMessage() {
        var projectNotFound = new ProjectNotFoundException(ID);
        var taskNotFound = new TaskNotFoundException(ID);
        var notEmpty = new ProjectNotEmptyException(ID);

        assertThat(projectNotFound.projectId()).isEqualTo(ID);
        assertThat(projectNotFound).hasMessage("No existe el proyecto con id " + ID);
        assertThat(taskNotFound.taskId()).isEqualTo(ID);
        assertThat(taskNotFound).hasMessage("No existe la tarea con id " + ID);
        assertThat(notEmpty.projectId()).isEqualTo(ID);
        assertThat(notEmpty).hasMessage("El proyecto con id " + ID + " todavía tiene tareas");
    }

    @Test
    void allDomainExceptionsShareABase() {
        assertThat(new DomainValidationException("x")).isInstanceOf(DomainException.class);
        assertThat(new ProjectNotFoundException(ID)).isInstanceOf(DomainException.class);
        assertThat(new TaskNotFoundException(ID)).isInstanceOf(DomainException.class);
        assertThat(new ProjectNotEmptyException(ID)).isInstanceOf(DomainException.class);
    }
}
