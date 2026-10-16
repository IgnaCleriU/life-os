package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullSource;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.boot.web.server.servlet.ConfigurableServletWebServerFactory;
import org.springframework.test.context.TestPropertySource;

/**
 * La API escucha solo en loopback salvo que se pida otra cosa. Un valor vacío
 * (p. ej. {@code LIFEOS_BIND_ADDRESS=} en un {@code .env}) no puede degradar a
 * {@code 0.0.0.0}. Independiente del entorno del shell.
 */
@TestPropertySource(properties = "lifeos.bind-address=")
class ServerBindingTest extends RestTestSupport {

    @Autowired
    WebServerFactoryCustomizer<ConfigurableServletWebServerFactory> bindAddressCustomizer;

    @Test
    void emptyPropertyBindsToLoopback() {
        var factory = new org.springframework.boot.tomcat.servlet.TomcatServletWebServerFactory();
        bindAddressCustomizer.customize(factory);
        assertThat(factory.getAddress().getHostAddress()).isEqualTo("127.0.0.1");
    }

    @ParameterizedTest
    @NullSource
    @ValueSource(strings = {"", "  ", "\t"})
    void blankResolvesToLoopback(String value) {
        assertThat(BindAddressConfiguration.resolve(value).getHostAddress()).isEqualTo("127.0.0.1");
    }

    @Test
    void explicitAddressIsTrimmedAndKept() {
        assertThat(BindAddressConfiguration.resolve("0.0.0.0").getHostAddress()).isEqualTo("0.0.0.0");
        assertThat(BindAddressConfiguration.resolve(" 127.0.0.1 ").getHostAddress()).isEqualTo("127.0.0.1");
    }

    @ParameterizedTest
    @ValueSource(strings = {"not-an-address", "999.1.1.1", "::zz"})
    void invalidAddressFailsStartup(String value) {
        assertThatThrownBy(() -> BindAddressConfiguration.resolve(value))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("LIFEOS_BIND_ADDRESS");
    }
}
