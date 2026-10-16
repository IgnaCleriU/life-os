package lifeos.application;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

/** {@link Change} distingue "no tocar el campo" de "ponerlo en null". */
class ChangeTest {

    @Test
    void unsetIsNotPresent() {
        assertThat(Change.<String>unset().isSet()).isFalse();
    }

    @Test
    void toNullIsPresentWithNullValue() {
        Change<String> change = Change.to(null);

        assertThat(change.isSet()).isTrue();
        assertThat(change.value()).isNull();
    }

    @Test
    void toValueCarriesIt() {
        assertThat(Change.to("x").value()).isEqualTo("x");
    }
}
