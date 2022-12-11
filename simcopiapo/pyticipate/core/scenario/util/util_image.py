import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from threading import Lock
lock = Lock()

def create_directional_arrow_png(left, text, arrow_color='0.2', text_color='w'):
    with lock:
        # Setup transparency
        ofc = plt.gcf().get_facecolor()
        ofca = []
        plt.gcf().set_facecolor((1,1,1,0))
        for ax in plt.gcf().axes:
            ofca.append(ax.get_facecolor())
            ax.set_facecolor((1,1,1,0))
        fig, ax = plt.subplots(1, figsize=(7.5,4))
        plt.xlim(0, 7.5), plt.ylim(0, 4)
        ax.axis('off')
        if left:
            ax.arrow(7.5, 2, -5, 0, color=arrow_color, width=2, head_width=4, head_length=2.5, antialiased=True)
            ax.text(1, 1.60, text, color=text_color, size=70)
        else:
            ax.arrow(0, 2, 5, 0, color=arrow_color, width=2, head_width=4, head_length=2.5, antialiased=True)
            ax.text(0.5, 1.6, text, color=text_color, size=70)
        # Save to bytes
        from io import BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, transparent=True, format='png')
        plt.close()
        bytes = buffer.getvalue()
        buffer.close()
        return bytes