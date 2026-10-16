package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;

/**
 * Por defecto la API escucha solo en loopback. Aunque ahora hay token (ADR
 * 0012), en {@code 0.0.0.0} cualquier equipo de la LAN llegaría al puerto de un
 * escritorio. Solo el contenedor lo cambia, con {@code LIFEOS_BIND_ADDRESS}.
 */
class ServerBindingTest extends RestTestSupport {

    @Value("${server.address:}")
    String serverAddress;

    @Test
    void listensOnLoopbackByDefault() {
        assertThat(serverAddress).isEqualTo("127.0.0.1");
    }
}
