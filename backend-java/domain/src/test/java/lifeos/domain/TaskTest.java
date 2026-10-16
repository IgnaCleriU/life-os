package lifeos.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/** Tests unitarios de la entidad Task (Java puro, sin DB ni mocks). */
class TaskTest {

    private static Task newTask() {
        return Task.create(UUID.randomUUID(), "Tarea");
    }

    @Test
    void createUsesDefaults() {
        UUID projectId = UUID.randomUUID();

        Task task = Task.create(projectId, "Escribir tests");

        assertThat(task.id()).isNotNull();
        assertThat(task.projectId()).isEqualTo(projectId);
        assertThat(task.title()).isEqualTo("Escribir tests");
        assertThat(task.status()).isSameAs(TaskStatus.TODO);
        assertThat(task.priority()).isSameAs(Priority.MEDIUM);
        assertThat(task.dueDate()).isNull();
        assertThat(task.description()).isNull();
        assertThat(task.createdAt()).isNotNull();
    }

    @Test
    void createWithAllFields() {
        LocalDate due = LocalDate.of(2026, 8, 1);

        Task task = Task.create(UUID.randomUUID(), "Tarea", Priority.HIGH, due, "detalle");

        assertThat(task.priority()).isSameAs(Priority.HIGH);
        assertThat(task.dueDate()).isEqualTo(due);
        assertThat(task.description()).isEqualTo("detalle");
    }

    @Test
    void createTruncatesTimestampToMicroseconds() {
        Task task = newTask();

        assertThat(task.createdAt()).isEqualTo(task.createdAt().truncatedTo(ChronoUnit.MICROS));
    }

    @Test
    void createNormalizesTitle() {
        assertThat(Task.create(UUID.randomUUID(), "  Tarea  ").title()).isEqualTo("Tarea");
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "   "})
    void createWithEmptyTitleThrows(String invalidTitle) {
        assertThatThrownBy(() -> Task.create(UUID.randomUUID(), invalidTitle))
                .isInstanceOf(DomainValidationException.class);
    }

    @Test
    void stateTransitions() {
        Task task = newTask();

        task.start();
        assertThat(task.status()).isSameAs(TaskStatus.DOING);
        task.complete();
        assertThat(task.status()).isSameAs(TaskStatus.DONE);
        task.reopen();
        assertThat(task.status()).isSameAs(TaskStatus.TODO);
    }

    @Test
    void completeIsIdempotent() {
        Task task = newTask();

        task.complete();
        task.complete();

        assertThat(task.status()).isSameAs(TaskStatus.DONE);
    }

    @Test
    void changePriority() {
        Task task = newTask();

        task.changePriority(Priority.HIGH);

        assertThat(task.priority()).isSameAs(Priority.HIGH);
    }

    @Test
    void rescheduleSetsAndClearsDueDate() {
        Task task = newTask();
        LocalDate due = LocalDate.of(2026, 8, 1);

        task.reschedule(due);
        assertThat(task.dueDate()).isEqualTo(due);

        task.reschedule(null);
        assertThat(task.dueDate()).isNull();
    }

    @Test
    void renameWithEmptyTitleThrows() {
        Task task = newTask();

        assertThatThrownBy(() -> task.rename("  "))
                .isInstanceOf(DomainValidationException.class);
    }

    @Test
    void moveToReassignsProject() {
        Task task = newTask();
        UUID destino = UUID.randomUUID();

        task.moveTo(destino);

        assertThat(task.projectId()).isEqualTo(destino);
    }

    @Test
    void describeSetsAndClearsDescription() {
        Task task = Task.create(UUID.randomUUID(), "Tarea", Priority.MEDIUM, null, "original");

        task.describe("nueva");
        assertThat(task.description()).isEqualTo("nueva");

        task.describe(null);
        assertThat(task.description()).isNull();
    }

    @Test
    void createIsNotDeleted() {
        Task task = newTask();

        assertThat(task.deletedAt()).isNull();
        assertThat(task.isDeleted()).isFalse();
    }

    @Test
    void deleteMarksAndRestoreClears() {
        Task task = newTask();

        task.delete();
        assertThat(task.isDeleted()).isTrue();
        assertThat(task.deletedAt()).isNotNull();

        task.restore();
        assertThat(task.isDeleted()).isFalse();
        assertThat(task.deletedAt()).isNull();
    }

    @Test
    void deleteIsIdempotentAndKeepsOriginalTimestamp() {
        Task task = newTask();
        task.delete();
        var primeraMarca = task.deletedAt();

        task.delete();

        assertThat(task.deletedAt()).isEqualTo(primeraMarca);
    }

    @Test
    void restoreIsIdempotent() {
        Task task = newTask();

        task.restore();

        assertThat(task.deletedAt()).isNull();
    }

    @Test
    void enumValuesMatchTheStoredStrings() {
        assertThat(TaskStatus.TODO.value()).isEqualTo("todo");
        assertThat(TaskStatus.DOING.value()).isEqualTo("doing");
        assertThat(TaskStatus.DONE.value()).isEqualTo("done");
        assertThat(Priority.LOW.value()).isEqualTo("low");
        assertThat(Priority.MEDIUM.value()).isEqualTo("medium");
        assertThat(Priority.HIGH.value()).isEqualTo("high");
        assertThat(TaskStatus.fromValue("doing")).isSameAs(TaskStatus.DOING);
        assertThat(Priority.fromValue("low")).isSameAs(Priority.LOW);
        assertThatThrownBy(() -> Priority.fromValue("urgent"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
