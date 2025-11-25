from content_robot import ContentRobot

config = {'generate_images': True}
robot = ContentRobot(config)

image = robot.generate_image_stable_diffusion(
    title="Teste de Imagem",
    keywords=["tecnologia", "inovação"]
)

print(f"Imagem gerada: {image}")