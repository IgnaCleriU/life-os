package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullSource;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * {@code LIFEOS_API_AUTH} como en Python ({@code Literal["enabled", "disabled"]}):
 * solo esas dos cadenas exactas; cualquier otra cosa, incluida la vacía, hace
 * fallar el arranque. Así el mismo {@code .env} se comporta igual en los dos backends.
 */
class AuthSettingTest {

    @Test
    void exactValuesAreAccepted() {
        assertThat(LocalGuardFilter.parseAuth("enabled")).isTrue();
        assertThat(LocalGuardFilter.parseAuth("disabled")).isFalse();
    }

    @ParameterizedTest
    @NullSource
    @ValueSource(strings = {"", " ", " enabled", "disabled ", "Enabled", "DISABLED", "off", "false", "0"})
    void anythingElseFailsStartup(String value) {
        assertThatThrownBy(() -> LocalGuardFilter.parseAuth(value))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("LIFEOS_API_AUTH");
    }
}
